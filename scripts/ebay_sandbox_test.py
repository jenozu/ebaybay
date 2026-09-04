import json
import os
from pathlib import Path

import requests

TOKEN_PATH = Path(os.getenv("EBAY_TOKEN_PATH", "data/token.json"))
BASE_URL = "https://api.sandbox.ebay.com"


def main():
    if not TOKEN_PATH.exists():
        raise SystemExit(f"Token file not found: {TOKEN_PATH}")

    data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    access_token = data.get("access_token")
    if not access_token:
        raise SystemExit("No access_token found in token file")

    response = requests.get(
        f"{BASE_URL}/sell/inventory/v1/getVersion",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )

    print("HTTP status:", response.status_code)
    if response.ok:
        print("Inventory API response:", response.text)
    else:
        print("Inventory API request failed")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
