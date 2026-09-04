import json
from pathlib import Path


class EbayTokenError(RuntimeError):
    pass


def load_access_token(token_path: Path) -> str:
    """Read the access token produced by the existing OAuth callback."""
    try:
        data = json.loads(Path(token_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EbayTokenError("eBay OAuth token is unavailable; reconnect the Sandbox account.") from exc
    token = data.get("access_token")
    if not token:
        raise EbayTokenError("The saved eBay OAuth response has no access token.")
    return token
