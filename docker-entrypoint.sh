#!/bin/bash
set -e

case "$1" in
  dashboard)
    # Servidor de producao (Gunicorn): varios workers+threads evitam 504 por bloqueio
    exec gunicorn \
      --workers 2 \
      --threads 4 \
      --timeout 300 \
      --bind 0.0.0.0:5000 \
      --access-logfile - \
      dashboard:app
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