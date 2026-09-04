from dataclasses import dataclass
from typing import Callable

import requests

from ...models import Listing, ListingAspect


class TaxonomyError(RuntimeError):
    pass


@dataclass(frozen=True)
class CategoryCandidate:
    category_id: str
    name: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"category_id": self.category_id, "name": self.name, "path": self.path}


@dataclass(frozen=True)
class CategoryAspect:
    name: str
    required: bool
    recommended: bool


class TaxonomyClient:
    _tree_cache: dict[tuple[str, str], str] = {}

    def __init__(self, *, environment: str, marketplace_id: str, access_token_provider: Callable[[], str], api_base: str = "", timeout: int = 30, session=None):
        default_base = "https://api.sandbox.ebay.com" if environment == "sandbox" else "https://api.ebay.com"
        self.base_url = (api_base or default_base).rstrip("/")
        self.marketplace_id = marketplace_id
        self.access_token_provider = access_token_provider
        self.timeout = timeout
        self.session = session or requests.Session()

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params=params,
                headers={"Authorization": f"Bearer {self.access_token_provider()}", "Accept": "application/json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise TaxonomyError(f"eBay Taxonomy request failed: {exc}") from exc

    def get_category_tree_id(self) -> str:
        key = (self.base_url, self.marketplace_id)
        if key not in self._tree_cache:
            payload = self._get("/commerce/taxonomy/v1/get_default_category_tree_id", {"marketplace_id": self.marketplace_id})
            tree_id = str(payload.get("categoryTreeId") or "").strip()
            if not tree_id:
                raise TaxonomyError("eBay returned no category tree ID.")
            self._tree_cache[key] = tree_id
        return self._tree_cache[key]

    def suggest_categories(self, query: str, limit: int = 5) -> list[CategoryCandidate]:
        payload = self._get(
            f"/commerce/taxonomy/v1/category_tree/{self.get_category_tree_id()}/get_category_suggestions",
            {"q": query},
        )
        candidates = []
        for suggestion in payload.get("categorySuggestions", [])[:limit]:
            category = suggestion.get("category", {})
            ancestors = suggestion.get("categoryTreeNodeAncestors", [])
            ancestor_names = [item.get("categoryName") for item in reversed(ancestors) if item.get("categoryName")]
            name = str(category.get("categoryName") or "").strip()
            category_id = str(category.get("categoryId") or "").strip()
            if category_id and name:
                candidates.append(CategoryCandidate(category_id, name, " > ".join([*ancestor_names, name])))
        return candidates

    def get_category_aspects(self, category_id: str) -> list[CategoryAspect]:
        payload = self._get(
            f"/commerce/taxonomy/v1/category_tree/{self.get_category_tree_id()}/get_item_aspects_for_category",
            {"category_id": category_id},
        )
        aspects = []
        for item in payload.get("aspects", []):
            name = str(item.get("localizedAspectName") or "").strip()
            constraint = item.get("aspectConstraint") or {}
            required = bool(constraint.get("aspectRequired"))
            recommended = required or str(constraint.get("aspectUsage") or "").upper() == "RECOMMENDED"
            if name and (required or recommended):
                aspects.append(CategoryAspect(name, required, recommended))
        return aspects


def taxonomy_query(listing: Listing) -> str:
    ai_terms = [str(term).strip() for term in (listing.ai_search_terms or []) if str(term).strip()]
    if ai_terms:
        return " ".join(ai_terms[:3])
    return " ".join(value.strip() for value in (listing.brand, listing.mpn, listing.model_number, listing.product_name, listing.title) if value and value.strip())


def sync_listing_aspects(listing: Listing, metadata: list[CategoryAspect]) -> None:
    existing = {aspect.name.casefold(): aspect for aspect in listing.aspects}
    attributes = {str(key).strip().casefold(): str(value).strip() for key, value in (listing.ai_detected_attributes or {}).items()}
    synced = []
    for definition in metadata:
        aspect = existing.get(definition.name.casefold())
        if aspect is None:
            aspect = ListingAspect(name=definition.name)
        aspect.required = definition.required
        aspect.recommended = definition.recommended
        if not aspect.value:
            aspect.value = attributes.get(definition.name.casefold()) or None
        synced.append(aspect)
    listing.aspects = synced


def select_category(listing: Listing, client: TaxonomyClient, candidate: CategoryCandidate) -> None:
    category_changed = listing.ebay_category_id != candidate.category_id
    listing.ebay_category_id = candidate.category_id
    listing.ebay_category_name = candidate.name
    listing.ebay_category_path = candidate.path
    if category_changed:
        sync_listing_aspects(listing, client.get_category_aspects(candidate.category_id))
