import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from statistics import median

from .ebay.browse import ActiveComparable


TOKEN_RE = re.compile(r"[a-z0-9]+")
CENT = Decimal("0.01")


@dataclass(frozen=True)
class ScoredComparable:
    item: ActiveComparable
    score: float


@dataclass(frozen=True)
class PricingSummary:
    low: Decimal
    high: Decimal
    median: Decimal
    quick_sale: Decimal
    recommended: Decimal
    high_target: Decimal
    confidence: str
    explanation: str


def _tokens(value: str | None) -> set[str]:
    return set(TOKEN_RE.findall((value or "").casefold()))


def _contains(title: str, value: str | None) -> bool:
    wanted = _tokens(value)
    return bool(wanted) and wanted <= _tokens(title)


def score_comparable(listing, item: ActiveComparable) -> float:
    title_tokens = _tokens(item.title)
    reference_tokens = _tokens(" ".join(filter(None, [listing.product_name, listing.title])))
    overlap = len(title_tokens & reference_tokens) / len(reference_tokens) if reference_tokens else 0
    score = 0.0
    score += 0.35 if _contains(item.title, listing.mpn) else 0
    score += 0.15 if _contains(item.title, listing.brand) else 0
    score += 0.15 if _contains(item.title, listing.model_number) else 0
    score += 0.10 if listing.condition and item.condition and listing.condition.casefold() in item.condition.casefold() else 0
    score += 0.15 if listing.ebay_category_id and item.category_id == listing.ebay_category_id else 0
    score += 0.10 * overlap
    return round(min(score, 1.0), 4)


def strongest_comparables(listing, items: list[ActiveComparable], *, currency: str = "CAD", minimum_score: float = 0.30, limit: int = 12) -> list[ScoredComparable]:
    scored = [ScoredComparable(item, score_comparable(listing, item)) for item in items if item.currency == currency]
    return sorted((entry for entry in scored if entry.score >= minimum_score), key=lambda entry: (-entry.score, entry.item.total_price, entry.item.item_id))[:limit]


def _price(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_pricing(comparables: list[ScoredComparable]) -> PricingSummary | None:
    if not comparables:
        return None
    prices = sorted(entry.item.total_price for entry in comparables)
    low, high, center = prices[0], prices[-1], Decimal(str(median(prices)))
    quick = max(low, center * Decimal("0.90"))
    upper = min(high, center * Decimal("1.10"))
    avg_score = sum(entry.score for entry in comparables) / len(comparables)
    spread = float((high - low) / center) if center else 1.0
    if len(comparables) >= 5 and avg_score >= 0.70 and spread <= 0.40:
        confidence = "HIGH"
    elif len(comparables) >= 3 and avg_score >= 0.50 and spread <= 0.75:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    explanation = f"{confidence.title()} confidence: {len(comparables)} relevant active listings, {avg_score:.0%} average similarity, and {spread:.0%} price spread."
    return PricingSummary(_price(low), _price(high), _price(center), _price(quick), _price(center), _price(upper), confidence, explanation)
