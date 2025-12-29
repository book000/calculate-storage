#!/bin/bash
set -eu

# root check
if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Required: git, python3, python3-venv
function check_command() {
  if ! type "$1" >/dev/null 2>&1; then
    read -p "Do you want to install $1? [y/n]: " yn
    if [ "$yn" = "y" ]; then
      if type apt >/dev/null 2>&1; then
        apt update
        apt install -y "$1"
      elif type yum >/dev/null 2>&1; then
        yum install -y "$1"
      else
        echo "Not found package manager"
        exit 1
      fi
    else
      echo "Please install $1"
      exit 1
    fi
  fi
}

check_command git
check_command python3

# docker command exists
if type docker >/dev/null 2>&1; then
  docker system prune -a -f
fi

mkdir -p /opt/calculate-storage
chmod 777 /opt/calculate-storage
cd /opt/calculate-storage || exit 1

# clone repository
if [ ! -d /opt/calculate-storage/.git ]; then
  git clone https://github.com/book000/calculate-storage.git .
else
  git pull
fi

# create venv and install requirements
if [ ! -d /opt/calculate-storage/venv ]; then
  python3 -mvenv venv
fi

venv/bin/pip install -r requirements.txt

export CALCULATE_STORAGE_LOG_DIR=/opt/calculate-storage/logs
venv/bin/python3 calculate_storage.py $ISSUE_NUMBER
