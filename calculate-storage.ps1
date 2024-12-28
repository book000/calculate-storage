# root check
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
  Write-Host "Please run as Administrator"
  exit 1
}

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

# docker command exists
if (Get-Command docker -ErrorAction SilentlyContinue) {
  docker system prune -a -f
}

$userFolder = [System.Environment]::GetFolderPath('UserProfile')
$projectPath = Join-Path $userFolder "calculate-storage"

New-Item -ItemType Directory -Force -Path $projectPath
Set-Location -Path $projectPath

# clone repository
if (-not (Test-Path "$projectPath\.git")) {
  git clone https://github.com/book000/calculate-storage.git .
}
else {
  git pull
}

# create venv and install requirements
if (-not (Test-Path "$projectPath\venv")) {
  python3 -m venv venv
}

.\venv\Scripts\pip install -r requirements.txt

.\venv\Scripts\python calculate-storage.py
