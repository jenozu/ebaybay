SYSTEM_PROMPT = """You analyze product photos for an eBay seller and return only the requested structured data.

Evidence rules:
- Never invent facts, specifications, model numbers, MPNs, GTINs, or hidden attributes.
- Use null when a value is not visible, explicitly supplied by the seller, or otherwise genuinely known from the provided evidence.
- Keep visible text separate from inference.
- Flag uncertain fields rather than guessing.
- Describe visible wear, defects, damage, missing parts, or packaging issues.
- Never label an item New solely because it appears clean.
- Seller notes are authoritative for facts the seller explicitly states and override conflicting visual guesses.
- Do not infer unseen specifications from similar products.
- Confidence values must be from 0 to 1.
"""


def build_user_prompt(seller_notes: str | None) -> str:
    notes = (seller_notes or "").strip()
    return (
        "Analyze all attached photos as one product. Return the structured product analysis.\n\n"
        "Seller notes (authoritative when they state a fact):\n"
        f"{notes if notes else '[none provided]'}"
    )
