# Operations runbook

## Production prerequisites

Set `EBAY_ENVIRONMENT=production` only after configuring the Production eBay keyset, Production RuName, accept/declined callback URLs, a non-default `SECRET_KEY`, password hash, token encryption key, and `SESSION_COOKIE_SECURE=true`. The app refuses unsafe Production startup.

Use HTTPS at the reverse proxy before connecting a real seller. Docker starts through Gunicorn and is configured with `restart: unless-stopped`.

## Backups and restore

Create a backup with `python scripts/backup_database.py`; schedule it daily using the configured `BACKUP_DIR`. It uses SQLite's backup API rather than copying a live file.

Test a restore against a stopped disposable copy first. To restore the configured database deliberately: `python scripts/restore_database.py --confirm-restore /path/to/backup.db`. Take a fresh backup before any real restore.

## Upload cleanup

Run `python scripts/cleanup_uploads.py` to preview old, unreferenced files. Only `python scripts/cleanup_uploads.py --apply` deletes them. Referenced listing photos are never selected.
