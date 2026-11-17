import datetime
import json
import re
import sys
import os
import socket
import psutil
import requests
import logging

GITHUB_REQUEST_TIMEOUT = (5, 30)

class GitHubRequestError(requests.exceptions.RequestException):
  def __init__(self, method, error):
    self.method = method
    self.error_type = type(error).__name__
    super().__init__(f"{method} request failed ({self.error_type})")

def _get_default_log_dir():
  if os.name == "nt":
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    return os.path.join(user_profile, "calculate-storage", "logs")
  return "/opt/calculate-storage/logs"

def _find_handler(root_logger, name):
  for handler in root_logger.handlers:
    if getattr(handler, "name", None) == name:
      return handler
  return None


def setup_logging():
  log_dir = os.environ.get("CALCULATE_STORAGE_LOG_DIR", _get_default_log_dir())
  try:
    os.makedirs(log_dir, exist_ok=True)
  except OSError as e:
    raise OSError(f"Failed to create log directory: {log_dir}: {e}") from e
  log_filename = datetime.date.today().strftime("%Y-%m-%d.log")
  log_path = os.path.join(log_dir, log_filename)
  log_path_abs = os.path.abspath(log_path)

  root_logger = logging.getLogger()
  file_handler = _find_handler(root_logger, "calculate-storage-file")
  stream_handler = _find_handler(root_logger, "calculate-storage-stream")

  if (
    file_handler
    and stream_handler
    and getattr(file_handler, "baseFilename", None) == log_path_abs
  ):
    return log_path
  if file_handler and getattr(file_handler, "baseFilename", None) == log_path_abs:
    if not stream_handler:
      for handler in list(root_logger.handlers):
        if (
          isinstance(handler, logging.StreamHandler)
          and handler is not file_handler
          and not isinstance(handler, logging.FileHandler)
        ):
          root_logger.removeHandler(handler)
          handler.close()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.name = "calculate-storage-stream"
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    return log_path

  if file_handler:
    root_logger.removeHandler(file_handler)
    file_handler.close()
  if stream_handler:
    root_logger.removeHandler(stream_handler)
    stream_handler.close()

  root_logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

  try:
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
  except OSError as e:
    raise OSError(f"Failed to create log file: {log_path}: {e}") from e
  file_handler.name = "calculate-storage-file"
  file_handler.setLevel(logging.DEBUG)
  file_handler.setFormatter(formatter)

  stream_handler = logging.StreamHandler()
  stream_handler.name = "calculate-storage-stream"
  stream_handler.setLevel(logging.INFO)
  stream_handler.setFormatter(formatter)

  root_logger.addHandler(file_handler)
  root_logger.addHandler(stream_handler)

  return log_path

class GitHubIssue:
  body = None
  storage_rows = None

  row_regex = re.compile(r"(?P<markdown>.*) <!-- calculate-storage#(?P<computer_name>.+)#(?P<drive>.+) -->")
  # Matches the size and drive type column, e.g. "1.90 TB (HDD)"
  size_regex = re.compile(r"^(?P<size>[0-9.]+ [TGMK]B) \((?P<drive_type>.+)\)$")

  def __init__(self, repo_name, issue_number, github_token):
    self.repo_name = repo_name
    self.issue_number = issue_number
    self.github_token = github_token

    self.body = self.__get_issue_body()
    self.storage_rows = self.__get_storage_rows()
    self.dirty_rows = set()

  def update_storage_row(self, computer_name, drive, usage):
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

        self.dirty_rows.add((computer_name, drive))
        return True

    return False

  def get_computer_drives(self, computer_name):
    computer_drives = []
    for storage_row in self.storage_rows:
      if storage_row["computer_name"] == computer_name:
        computer_drives.append(storage_row["drive"])
    return computer_drives

  def update_issue_body(self):
    self.body = self.__get_issue_body()

    rows = self.body.split("\n")
    new_rows = []
    for row in rows:
      m = self.row_regex.match(row)
      if m is None:
        new_rows.append(row)
        continue

      computer_name = m.group("computer_name")
      drive = m.group("drive")
      if (computer_name, drive) not in self.dirty_rows:  # noqa: E111
        new_rows.append(row)
        continue
      for storage_row in self.storage_rows:
        if storage_row["computer_name"] == computer_name and storage_row["drive"] == drive:
          new_rows.append(storage_row["markdown"]["raw"] + f" <!-- calculate-storage#{computer_name}#{drive} -->")
          break
      else:
        new_rows.append(row)

    self.body = "\n".join(new_rows)

    try:
      response = requests.patch(
        f"https://api.github.com/repos/{self.repo_name}/issues/{self.issue_number}",
        headers={
          "Authorization" : f"token {self.github_token}"
        },
        json={
          "body": self.body
        },
        timeout=GITHUB_REQUEST_TIMEOUT
      )
    except requests.exceptions.RequestException as e:
      raise GitHubRequestError("PATCH", e) from e

    if response.status_code != 200:
      raise Exception(f"Failed to update issue body: {response.text}")

    self.dirty_rows.clear()
    return True

  def __get_issue_body(self):
    url = f"https://api.github.com/repos/{self.repo_name}/issues/{self.issue_number}"
    headers = {
      "Authorization": f"token {self.github_token}"
    }

    try:
      response = requests.get(url, headers=headers, timeout=GITHUB_REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
      raise GitHubRequestError("GET", e) from e
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

      # Split the table part on "|"; a valid row yields 7 parts (empty edges + 5 columns)
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
    return os.environ.get('COMPUTERNAME') or socket.gethostname()
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
  log_path = setup_logging()
  logging.info(f"Logging to {log_path}")

  repo_name = "book000/book000"
  if os.environ.get("GITHUB_REPOSITORY") is not None:
    repo_name = os.environ["GITHUB_REPOSITORY"]

  issue_number = sys.argv[1] if len(sys.argv) > 1 else None
  if issue_number is None:
    logging.error("Please input issue number")
    return 1
  if not is_valid_issue_number(issue_number):
    logging.error("Invalid issue number")
    return 1

  logging.info(f"Issue number: {issue_number}")

  github_token = get_github_token()

  try:
    github_issue = GitHubIssue(repo_name, issue_number, github_token)
  except GitHubRequestError as e:
    logging.error(f"GitHub API {e.method} request failed ({e.error_type})")
    return 1

  hostname = get_real_hostname()
  drives = github_issue.get_computer_drives(hostname)
  if len(drives) == 0:
    logging.warning(f"No drives found ({hostname})")
    return 1

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
  try:
    github_issue.update_issue_body()
  except GitHubRequestError as e:
    logging.error(f"GitHub API {e.method} request failed ({e.error_type})")
    return 1
  return 0

if __name__ == "__main__":
  sys.exit(main())
