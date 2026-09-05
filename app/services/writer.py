"""Deterministic, evidence-grounded listing copy generation."""
from html import escape
import re


TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def _clean(value):
    return " ".join(str(value or "").split())


def _tokens(value):
    return TOKEN_RE.findall(_clean(value).casefold())


def generate_title(listing, limit=80):
    """Build a non-repetitive title only from persisted listing identifiers."""
    seen, words = set(), []
    for value in (listing.brand, listing.mpn, listing.model_number, listing.product_name):
        for word in _clean(value).split():
            key = tuple(_tokens(word)) or (word.casefold(),)
            if key and not any(token in seen for token in key):
                words.append(word)
                seen.update(key)
    title = " ".join(words)
    if len(title) <= limit:
        return title or None
    kept = []
    for word in words:
        candidate = " ".join([*kept, word])
        if len(candidate) > limit:
            break
        kept.append(word)
    return " ".join(kept) or title[:limit]


def _line(label, value):
    value = _clean(value)
    return f"<li><strong>{escape(label)}:</strong> {escape(value)}</li>" if value else ""


def generate_description(listing):
    """Simple escaped HTML; never reads comparable listing content."""
    details = [
        _line("Item", listing.product_name), _line("Brand", listing.brand),
        _line("Model", listing.model_number), _line("MPN", listing.mpn),
        _line("Condition", listing.condition), _line("Quantity", listing.quantity),
    ]
    aspects = [_line(aspect.name, aspect.value) for aspect in listing.aspects if aspect.value]
    sections = []
    if any(details): sections.append("<h2>Item details</h2><ul>" + "".join(item for item in details if item) + "</ul>")
    if aspects: sections.append("<h2>Item specifics</h2><ul>" + "".join(aspects) + "</ul>")
    if _clean(listing.seller_notes): sections.append("<h2>Seller notes</h2><p>" + escape(listing.seller_notes).replace("\n", "<br>") + "</p>")
    observations = [_clean(item) for item in (listing.ai_visible_observations or []) if _clean(item)]
    if observations: sections.append("<h2>Visible observations</h2><ul>" + "".join(f"<li>{escape(item)}</li>" for item in observations) + "</ul>")
    return "\n".join(sections) or None


def generate_condition_description(listing):
    parts = []
    if _clean(listing.condition): parts.append(f"Condition: {_clean(listing.condition)}.")
    if _clean(listing.seller_notes): parts.append(f"Seller notes: {_clean(listing.seller_notes)}")
    observations = [_clean(item) for item in (listing.ai_visible_observations or []) if _clean(item)]
    if observations: parts.append("Visible observations: " + "; ".join(observations))
    return " ".join(parts) or None
