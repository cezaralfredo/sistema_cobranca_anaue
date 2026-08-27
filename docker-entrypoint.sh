#!/bin/bash
set -e

case "$1" in
  dashboard)
    exec python dashboard.py
    ;;
  automation)
    exec python main.py
    ;;
  *)
    echo "Usage: $0 {dashboard|automation}"
    exit 1
    ;;
esac