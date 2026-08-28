#!/bin/bash
set -e

case "$1" in
  dashboard)
    exec python dashboard.py
    ;;
  automation)
    exec python main.py
    ;;
  scheduler)
    exec python scheduler.py
    ;;
  *)
    echo "Usage: $0 {dashboard|automation|scheduler}"
    exit 1
    ;;
esac