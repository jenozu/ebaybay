import os

REQUIRED = [
    "EBAY_CLIENT_ID",
    "EBAY_CLIENT_SECRET",
    "EBAY_RUNAME",
    "EBAY_MARKETPLACE_ID",
]

missing = []
for key in REQUIRED:
    if os.getenv(key):
        print(f"{key}: SET")
    else:
        print(f"{key}: MISSING")
        missing.append(key)

raise SystemExit(1 if missing else 0)
