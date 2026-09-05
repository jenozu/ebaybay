#!/bin/sh
set -eu
flask --app wsgi.py db upgrade
exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" --access-logfile - --error-logfile - --capture-output wsgi:app
