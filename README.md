# calculate-storage

Uses a GitHub Issue as a dashboard for the disk usage of multiple machines. Run `calculate_storage.py` on each machine: it reads the Markdown table in the target Issue body, measures the drives registered for the current host with [psutil](https://github.com/giampaolo/psutil), and rewrites only those rows through the GitHub API.

## Requirements

- Python 3.10 or later (CI covers 3.10 to 3.13 and the latest 3.x on Ubuntu and Windows)
- Dependencies in `requirements.txt` (`psutil`, `requests`)
- A GitHub token that can read and edit the target Issue

## Setup

```bash
pip install -r requirements.txt
mkdir -p data
# write the token into the file with an editor, then restrict it
chmod 600 data/github_token.txt
```

The token is read from `data/github_token.txt` relative to the current working directory (not from an environment variable). `data/` and `results/` are git-ignored; never commit them.

## Issue format

Each managed row is a Markdown table row followed by an HTML comment marker that identifies the host and the drive:

```
| ✅ | hostname1 | C: | 1.20 TB (75.0%) | 1.60 TB (SSD) | <!-- calculate-storage#hostname1#C -->
```

- Row marker: `<!-- calculate-storage#<computer_name>#<drive> -->`. `computer_name` must equal the host name reported by the machine (`COMPUTERNAME` on Windows, falling back to `socket.gethostname()` when it is unset or empty; `os.uname()[1]` elsewhere). `drive` is passed as is to `psutil.disk_usage()`, so it can differ from the displayed drive column (for example marker `C` with display `C:`, or a mount point such as `/`).
- Table part: `| mark | computer | drive | used | size (type) |`. The size column must look like `1.60 TB (SSD)` (`[TGMK]B` unit followed by the drive type in parentheses).
- Rows without a marker are kept unchanged. A marker row whose table part does not split into 7 `|`-separated parts or whose size column does not match the format above is not parsed, so it is never updated, but it is kept unchanged when the body is rewritten. Keep the format exact for the row to be updated.
- Add the rows yourself; the tool never creates new ones. After an update the mark is 🔴 when usage is above 90%, otherwise ✅.

## Usage

```bash
python calculate_storage.py <ISSUE_NUMBER>
```

| Variable | Default | Meaning |
|---|---|---|
| `GITHUB_REPOSITORY` | `book000/book000` | `owner/repo` that holds the Issue |
| `CALCULATE_STORAGE_LOG_DIR` | Unix: `/opt/calculate-storage/logs`, Windows: `%USERPROFILE%\calculate-storage\logs` | Log directory (created if missing) |

The log directory must be writable: with the default on Unix you need write access to `/opt/calculate-storage/logs`, so set `CALCULATE_STORAGE_LOG_DIR` when running as a normal user.

### Output

- Issue: the successfully measured rows of the Issue body are updated through `PATCH /repos/{repo}/issues/{number}`. The body is fetched again just before writing to preserve other rows, but changes made between that fetch and the PATCH can still be overwritten.
- Log: `YYYY-MM-DD.log` in the log directory (DEBUG level; the console shows INFO and above).
- Results: `results/<hostname>_<YYYYMMDD>.txt` in the working directory, one JSON object per line (JSON Lines despite the `.txt` extension) with `drive`, `used`, `total`, `percent`, `used_size`, `total_size` and `update_result`.

If the host has no rows in the Issue, the tool logs a warning and exits with status 1 without writing. A drive for which `psutil.disk_usage()` fails is logged and skipped.

Exit status: the tool exits with 0 when the update flow completes, and with status 1 when the Issue number is missing or invalid or when the host has no rows in the Issue.

## Deployment scripts

`calculate-storage.sh` (Linux/Unix, run as root) and `calculate-storage.ps1` (Windows PowerShell) clone or update this repository (`/opt/calculate-storage` or `%USERPROFILE%\calculate-storage`), create a virtual environment, install the requirements, and run the tool. Both read the Issue number from the `ISSUE_NUMBER` environment variable and expect `data/github_token.txt` inside that directory.

```bash
sudo ISSUE_NUMBER=123 bash calculate-storage.sh
```

```powershell
$env:ISSUE_NUMBER = "123"; .\calculate-storage.ps1
```

Warning: both scripts run `docker system prune -a -f` when `docker` is available, which removes all unused Docker images, stopped containers, unused networks and build cache on the host before collecting disk usage. The shell script also creates `/opt/calculate-storage` with mode 755 (owner-writable only; keep the token file readable by its owner only, e.g. `chmod 600 data/github_token.txt`), offers to install a missing `git` or `python3` through `apt`/`yum` after asking for confirmation, and installs `python3-venv` through `apt` without asking when `ensurepip` is unavailable.

## Development

```bash
python -m unittest discover -s . -p "test_*.py"
```

The tests mock GitHub and psutil and need no network or token. Python files use 2-space indentation (see `.editorconfig`). See `AGENTS.md` for contributor and agent guidance.

## License

This project is licensed under the [MIT License](LICENSE).
