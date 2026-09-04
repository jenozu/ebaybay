from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Callable

import requests

from ...models import Listing


class BrowseError(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchTerm:
    query: str
    strategy: str


@dataclass(frozen=True)
class ActiveComparable:
    item_id: str
    title: str
    price: Decimal
    shipping_cost: Decimal
    currency: str
    url: str | None
    condition: str | None
    category_id: str | None
    search_query: str

    @property
    def total_price(self) -> Decimal:
        return self.price + self.shipping_cost


def generate_search_terms(listing: Listing) -> list[SearchTerm]:
    candidates = []
    if listing.mpn:
        candidates.append(SearchTerm(listing.mpn.strip(), "exact_mpn"))
    if listing.brand and listing.mpn:
        candidates.append(SearchTerm(f"{listing.brand.strip()} {listing.mpn.strip()}", "brand_mpn"))
    if listing.brand and listing.model_number:
        candidates.append(SearchTerm(f"{listing.brand.strip()} {listing.model_number.strip()}", "brand_model"))
    for term in listing.ai_search_terms or []:
        if str(term).strip():
            candidates.append(SearchTerm(str(term).strip(), "ai_term"))
    broad = " ".join(value.strip() for value in (listing.brand, listing.product_name) if value and value.strip())
    if broad:
        candidates.append(SearchTerm(broad, "broad"))
    elif listing.product_name or listing.title:
        candidates.append(SearchTerm((listing.product_name or listing.title).strip(), "broad"))

    unique, result = set(), []
    for candidate in candidates:
        key = candidate.query.casefold()
        if key not in unique:
            unique.add(key)
            result.append(candidate)
    return result


class BrowseClient:
    def __init__(self, *, environment: str, marketplace_id: str, access_token_provider: Callable[[], str], api_base: str = "", timeout: int = 30, session=None):
        default_base = "https://api.sandbox.ebay.com" if environment == "sandbox" else "https://api.ebay.com"
        self.base_url = (api_base or default_base).rstrip("/")
        self.marketplace_id = marketplace_id
        self.access_token_provider = access_token_provider
        self.timeout = timeout
        self.session = session or requests.Session()

    def search(self, term: SearchTerm, limit: int = 25) -> list[ActiveComparable]:
        try:
            response = self.session.get(
                f"{self.base_url}/buy/browse/v1/item_summary/search",
                params={"q": term.query, "limit": limit, "filter": "buyingOptions:{FIXED_PRICE}"},
                headers={"Authorization": f"Bearer {self.access_token_provider()}", "Accept": "application/json", "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise BrowseError(f"eBay Browse request failed: {exc}") from exc
        return [item for raw in payload.get("itemSummaries", []) if (item := self._normalize(raw, term.query))]

    @staticmethod
    def _money(raw: dict | None) -> tuple[Decimal, str] | None:
        if not raw:
            return None
        try:
            value = Decimal(str(raw["value"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (KeyError, InvalidOperation):
            return None
        return value, str(raw.get("currency") or "").upper()

    @classmethod
    def _normalize(cls, raw: dict, query: str) -> ActiveComparable | None:
        money = cls._money(raw.get("price"))
        if not money or not raw.get("itemId") or not raw.get("title"):
            return None
        price, currency = money
        shipping_cost = Decimal("0.00")
        shipping_values = [money[0] for option in (raw.get("shippingOptions") or []) if (money := cls._money(option.get("shippingCost"))) and money[1] == currency]
        if shipping_values:
            shipping_cost = min(shipping_values)
        categories = raw.get("categories") or []
        return ActiveComparable(
            item_id=str(raw["itemId"]), title=str(raw["title"]), price=price,
            shipping_cost=shipping_cost, currency=currency, url=raw.get("itemWebUrl"),
            condition=raw.get("condition"), category_id=str(categories[0].get("categoryId")) if categories and categories[0].get("categoryId") else None,
            search_query=query,
        )


def search_active_comparables(listing: Listing, client: BrowseClient, minimum_results: int = 5, relevance_filter: Callable[[list[ActiveComparable]], list] | None = None) -> list[ActiveComparable]:
    found: dict[str, ActiveComparable] = {}
    for term in generate_search_terms(listing):
        is_broad = term.strategy in {"ai_term", "broad"}
        relevant_count = len(relevance_filter(list(found.values()))) if relevance_filter else len(found)
        if is_broad and relevant_count >= minimum_results:
            break
        for item in client.search(term):
            found.setdefault(item.item_id, item)
    return list(found.values())
