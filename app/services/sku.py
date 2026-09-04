from datetime import datetime, timezone
from uuid import uuid4


def generate_sku() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"EBAY-{stamp}-{uuid4().hex[:10].upper()}"
