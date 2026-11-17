# Required: git, python3, python3-venv
function Test-Command {
  param (
    [string]$command
  )
  if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
    Write-Host "Please install $command"
    exit 1
  }
}

Test-Command git
Test-Command python3

# Destructive: removes all unused images, not only dangling ones
if (Get-Command docker -ErrorAction SilentlyContinue) {
  docker system prune -a -f
}

$userFolder = [System.Environment]::GetFolderPath('UserProfile')
$projectPath = Join-Path $userFolder "calculate-storage"

New-Item -ItemType Directory -Force -Path $projectPath | Out-Null
Set-Location -Path $projectPath -ErrorAction Stop
$env:CALCULATE_STORAGE_LOG_DIR = Join-Path $projectPath "logs"

# clone repository
if (-not (Test-Path "$projectPath\.git")) {
  git clone https://github.com/book000/calculate-storage.git .
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
else {
  git pull
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

# create venv and install requirements
if (-not (Test-Path "$projectPath\venv")) {
  python3 -m venv venv
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

.\venv\Scripts\pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

.\venv\Scripts\python calculate_storage.py $env:ISSUE_NUMBER
exit $LASTEXITCODE
