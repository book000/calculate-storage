import datetime
import json
import re
import sys
import os
import psutil
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

class GitHubIssue:
  body = None
  storage_rows = None

  row_regex = re.compile(r"(?P<markdown>.*) <!-- calculate-storage#(?P<computer_name>.+)#(?P<drive>.+) -->")
  # 1.9TB (HDD) というサイズ + ドライブの種類を取得するための正規表現
  size_regex = re.compile(r"^(?P<size>[0-9.]+ [TGMK]B) \((?P<drive_type>.+)\)$")

  def __init__(self, repo_name, issue_number, github_token):
    self.repo_name = repo_name
    self.issue_number = issue_number
    self.github_token = github_token

    self.body = self.__get_issue_body()
    self.storage_rows = self.__get_storage_rows()

  def update_storage_row(self, computer_name, drive, usage):
    # self.storage_rows から computer_name と drive が一致する行を取得する
    # その行の checkmark、used、size を更新する
    used_size = self.get_human_readable_size(usage.used)
    used_percent = usage.percent
    total_size = self.get_human_readable_size(usage.total)

    checkmark = "🔴" if used_percent > 90 else "✅"

    logging.info(f"{checkmark} {drive}: {used_size} / {total_size} ({used_percent}%)")

    for storage_row in self.storage_rows:
      if storage_row["computer_name"] == computer_name and storage_row["drive"] == drive:
        storage_row["markdown"]["checkmark"] = checkmark
        storage_row["markdown"]["used"] = f"{used_size} ({used_percent}%)"
        storage_row["markdown"]["size"] = total_size
        storage_row["markdown"]["raw"] = f"| {storage_row['markdown']['checkmark']} | {storage_row['markdown']['computer_name']} | {storage_row['markdown']['drive']} | {storage_row['markdown']['used']} | {storage_row['markdown']['size']} ({storage_row['markdown']['drive_type']}) |"

        return True

    return False

  def get_computer_drives(self, computer_name):
    computer_drives = []
    for storage_row in self.storage_rows:
      if storage_row["computer_name"] == computer_name:
        computer_drives.append(storage_row["drive"])
    return computer_drives

  def update_issue_body(self):
    # self.storage_rows の内容を元に、issue の本文を更新する
    # <!-- calculate-storage#computer_name#drive --> というコメントを探して、その行を更新する
    rows = self.body.split("\n")
    new_rows = []
    for row in rows:
      m = self.row_regex.match(row)
      if m is None:
        new_rows.append(row)
        continue

      computer_name = m.group("computer_name")
      drive = m.group("drive")
      for storage_row in self.storage_rows:
        if storage_row["computer_name"] == computer_name and storage_row["drive"] == drive:
          new_rows.append(storage_row["markdown"]["raw"] + f" <!-- calculate-storage#{computer_name}#{drive} -->")
          break

    self.body = "\n".join(new_rows)

    response = requests.patch(
      f"https://api.github.com/repos/{self.repo_name}/issues/{self.issue_number}",
      headers={
        "Authorization" : f"token {self.github_token}"
      },
      json={
        "body": self.body
      }
    )

    if response.status_code != 200:
      raise Exception(f"Failed to update issue body: {response.text}")

    return True

  def __get_issue_body(self):
    url = f"https://api.github.com/repos/{self.repo_name}/issues/{self.issue_number}"
    headers = {
      "Authorization": f"token {self.github_token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
      raise Exception(f"Failed to get issue body: {response.text}")

    return response.json()["body"]

  def __get_storage_rows(self):
    storage_rows = []
    lines = self.body.split("\n")

    for line in lines:
      m = self.row_regex.match(line)
      if m is None:
        continue

      # | で split して、それぞれの値を取得する
      markdown = m.group("markdown")
      split_markdown = markdown.split("|")
      if len(split_markdown) != 7:
        continue
      checkmark = split_markdown[1].strip()
      view_computer_name = split_markdown[2].strip()
      drive = split_markdown[3].strip()
      used = split_markdown[4].strip()
      size_raw = split_markdown[5].strip()
      match_size = self.size_regex.match(size_raw)
      if match_size is None:
        continue
      size = match_size.group("size")
      drive_type = match_size.group("drive_type")

      storage_rows.append({
        "markdown": {
          "checkmark": checkmark,
          "computer_name": view_computer_name,
          "drive": drive,
          "used": used,
          "size": size,
          "drive_type": drive_type,
          "raw": markdown
        },
        "computer_name": m.group("computer_name"),
        "drive": m.group("drive")
      })

    return storage_rows

  def get_human_readable_size(self, size):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit = 0
    while size >= 1024:
      size /= 1024
      unit += 1
    return f'{size:.2f} {units[unit]}'

def is_valid_issue_number(issue_number):
  if issue_number is None:
    return False

  if not issue_number.isdigit():
    return False

  return True

def get_real_hostname():
  if os.name == 'nt':
    return os.environ['COMPUTERNAME']
  else:
    return os.uname()[1]

def get_github_token():
  if not os.path.exists("data/github_token.txt"):
    raise Exception("Please create data/github_token.txt")

  with open("data/github_token.txt", "r", encoding="utf-8") as f:
    return f.read().strip()

def save_results(hostname, results):
  date = datetime.datetime.now().strftime('%Y%m%d')
  path = f"results/{hostname}_{date}.txt"
  try:
    if not os.path.exists("results"):
      os.makedirs("results")
  except OSError as e:
    logging.error(f"Failed to create results directory: {e}")
    raise

  with open(path, "w", encoding="utf-8") as f:
    for result in results:
      f.write(json.dumps(result, ensure_ascii=False) + "\n")

def main():
  repo_name = "book000/book000"
  if os.environ.get("GITHUB_REPOSITORY") is not None:
    repo_name = os.environ["GITHUB_REPOSITORY"]

  issue_number = sys.argv[1] if len(sys.argv) > 1 else None
  if issue_number is None:
    logging.error("Please input issue number")
    return
  if not is_valid_issue_number(issue_number):
    logging.error("Invalid issue number")
    return

  logging.info(f"Issue number: {issue_number}")

  github_token = get_github_token()

  github_issue = GitHubIssue(repo_name, issue_number, github_token)

  hostname = get_real_hostname()
  drives = github_issue.get_computer_drives(hostname)
  if len(drives) == 0:
    logging.warning(f"No drives found ({hostname})")
    return

  results = []
  for drive in drives:
    try:
      usage = psutil.disk_usage(drive)
    except OSError as e:
      logging.error(f"Failed to get disk usage for {drive}: {e}")
      continue

    update_result = github_issue.update_storage_row(hostname, drive, usage)
    if not update_result:
      logging.error(f"Failed to update {drive}")

    results.append({
      "drive": drive,
      "used": usage.used,
      "total": usage.total,
      "percent": usage.percent,
      "used_size": github_issue.get_human_readable_size(usage.used),
      "total_size": github_issue.get_human_readable_size(usage.total),
      "update_result": update_result
    })

  save_results(hostname, results)

  logging.info("Update issue body")
  github_issue.update_issue_body()

if __name__ == "__main__":
  main()