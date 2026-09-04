# eBay AI Listing Assistant
## MVP + Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** September 3, 2026  
**Status:** Build-ready MVP specification  
**Primary marketplace target:** eBay Canada (`EBAY_CA`)  
**Initial deployment:** Existing Hostinger VPS, isolated Docker project  
**Primary goal:** Turn product photos + minimal seller notes into a reviewed, validated eBay listing that can be published with one explicit approval.

---

# 1. Executive Decision

## 1.1 Where this should live

**Do not buy another VPS for the MVP.**

Build this as a **new Git repository and a new Docker project/folder on the existing Hostinger VPS**.

Recommended logical layout:

```text
docker/
├── rf-scanner/
├── other-existing-project/
└── ebaybay/
```

The exact parent directory does not matter. What matters is that this app has:

- its own Git repository;
- its own `.env`;
- its own `docker-compose.yml`;
- its own application container;
- its own persistent data volume;
- its own upload/storage volume;
- its own internal port;
- its own domain/subdomain;
- its own logs;
- no shared source code with unrelated projects.

---

# 2. Product Vision

Create a private seller assistant that dramatically reduces the repetitive work involved in making eBay listings.

The seller should be able to:

1. upload several photos;
2. optionally type a few notes;
3. let AI identify and describe the item;
4. automatically obtain likely eBay category and item-specific requirements;
5. research comparable active listings;
6. receive a recommended title, price, condition, description, category, and item specifics;
7. edit anything that is wrong;
8. run validation;
9. approve the listing;
10. publish it to eBay.

The software should never require the seller to manually rewrite the same standard shipping, returns, payment, or inventory-location information for every listing.

---

# 3. Problem Statement

Creating an eBay listing manually requires repetitive work:

- uploading pictures;
- identifying the item;
- reading model/part numbers;
- selecting a category;
- filling required item specifics;
- writing an optimized title;
- writing a description;
- selecting condition;
- researching similar listings;
- setting a price;
- selecting payment policies;
- selecting shipping policies;
- selecting return policies;
- reviewing the listing;
- publishing it.

For a seller listing many different items, the time cost compounds quickly.

The MVP should reduce this to:

```text
PHOTOS + OPTIONAL NOTES
        ↓
GENERATE
        ↓
REVIEW
        ↓
PUBLISH
```

---

# 4. Product Principles

1. Human approval before publishing.
2. Every AI-generated field remains editable.
3. Never invent product facts; use unknown/null when uncertain.
4. Prefer deterministic eBay metadata over AI guesses.
5. The app is the source of truth for drafts.
6. Use official eBay APIs first; Playwright is fallback only.
7. Build incrementally; each phase stays runnable, tested, documented, and committed.

---

# 5. MVP User

A single authenticated eBay seller. The MVP does not require teams, billing, public registration, or customer-facing pages.

---

# 6. Core MVP Workflow

```text
1. CREATE LISTING
        ↓
2. UPLOAD PHOTOS
        ↓
3. OPTIONAL SELLER NOTES
        ↓
4. AI PRODUCT ANALYSIS
        ↓
5. PRODUCT IDENTITY CANDIDATE
        ↓
6. EBAY CATEGORY SUGGESTION
        ↓
7. EBAY REQUIRED ASPECTS
        ↓
8. AI FILLS SUPPORTED ASPECTS
        ↓
9. ACTIVE COMPARABLE RESEARCH
        ↓
10. PRICE RECOMMENDATION
        ↓
11. LISTING GENERATION
        ↓
12. REVIEW / EDIT
        ↓
13. VALIDATE
        ↓
14. APPROVE
        ↓
15. UPLOAD IMAGES TO EBAY
        ↓
16. CREATE/UPDATE INVENTORY ITEM
        ↓
17. CREATE OFFER
        ↓
18. FINAL PUBLISH CONFIRMATION
        ↓
19. PUBLISH OFFER
        ↓
20. SAVE EBAY LISTING ID + URL
```

---

# 7. MVP Scope

Included: single-user login, eBay OAuth, image upload, multiple images, AI product analysis, visible-text extraction, seller notes, title/description/condition generation, category suggestion, Taxonomy lookup, category aspects, item specifics, current active comparable research, price recommendation, editable review, validation, drafts, Media API image upload, Inventory Item creation, Offer creation, explicit publish confirmation, Publish Offer, listing history, logging, Docker, persistent DB/uploads, Sandbox and Production configuration.

Explicitly excluded from MVP: sold/completed comps, cross-posting, order fulfillment, labels, accounting, customer messaging, auctions, variations, multi-user permissions, bulk CSV, unattended publishing, Telegram approvals, image enhancement, scheduled listing, repricing, promotions, advanced analytics.

---

# 8. Recommended Technology Stack

```text
Python 3.12+
Flask
SQLAlchemy
Alembic
requests or httpx
Pydantic
Jinja2
Bootstrap
vanilla JavaScript
SQLite
Docker / Docker Compose
HTTPS reverse proxy
```

Use a vision-capable LLM behind an internal provider abstraction.

---

# 9. Core Data Model

## Listing

```text
id, uuid, sku, status, seller_notes,
identified_product, brand, model, mpn, gtin,
condition, condition_description,
title, description,
category_id, category_name,
currency, recommended_price, final_price, quantity,
ai_confidence, ai_raw_json,
ebay_offer_id, ebay_listing_id, ebay_listing_url,
created_at, updated_at, approved_at, published_at
```

## ListingImage

```text
id, listing_id, local_path, display_order, original_filename, mime_type,
ebay_image_id, ebay_image_url, created_at
```

## ListingAspect

```text
id, listing_id, name, value, required, recommended, source
```

## ComparableListing

```text
id, listing_id, ebay_item_id, title, price, currency, condition,
shipping_cost, item_url, similarity_score, created_at
```

## eBayConnection

```text
id, environment, marketplace_id, encrypted_refresh_token,
access_token_expires_at, connected_at, updated_at
```

---

# 10. Listing State Machine

```text
NEW → ANALYZING → DRAFT → NEEDS_REVIEW → READY → EBAY_STAGED → PUBLISHED
```

Failure states:

```text
ANALYSIS_FAILED
VALIDATION_FAILED
EBAY_SYNC_FAILED
PUBLISH_FAILED
```

---

# 11. AI Product Analysis

Inputs: uploaded images, seller notes, marketplace, optional SKU.

Structured output should include product identity, brand, model, MPN, GTIN, condition suggestion/confidence/observations, visible text, search terms, attributes, uncertain fields, and overall confidence.

Rules: do not infer unseen specs; never invent MPNs; distinguish visible text from inference; use null when unknown; flag uncertainty; describe visible damage; do not call an item new merely because it looks clean; seller notes override visual guesses about known facts.

---

# 12. Category + Item Specifics

Two-stage category selection: AI suggests plain-English category/search terms; eBay Taxonomy validates/selects a leaf category and returns category aspects. Store category ID/name/path. User can override.

For item specifics: retrieve aspects, mark required/recommended, map AI attributes to aspect names, and prominently show required missing values. The validator—not AI—controls publish eligibility.

---

# 13. Active Comparable Search + Pricing

Use Browse API for active/purchasable listings. Search order: exact MPN; brand + MPN; brand + model; broader product terms. Score similarity using MPN, brand, model, condition, category, and title overlap. Label results **Active Comparables**, never sold comps.

Pricing output should show comparable range/median, quick-sale, recommended, high target, and confidence. Never overwrite a user's manual final price.

---

# 14. Listing Generation

Generate title/description after product/category metadata are available. Title must be factual, concise, search-friendly, and within eBay limits. Description should use a consistent factual template. Do not claim compatibility unless verified.

---

# 15. Review + Validation

Review screen must expose photos, product identity, category, condition, title, pricing, aspects, and description. All generated fields editable. Actions: Save Draft, Regenerate, Validate, Approve. After approval: Stage on eBay. After staging: Publish to eBay with explicit confirmation.

Validator checks local required fields, eBay-required aspects/policies/location/marketplace/format, title length, duplicate SKU, price precision, condition validity, image upload status, and OAuth usability.

---

# 16. eBay Integration Architecture

Use one client layer under `app/services/ebay/`:

```text
oauth.py
taxonomy.py
browse.py
account.py
media.py
inventory.py
```

Do not scatter raw eBay calls through routes.

---

# 17. OAuth + Seller Setup

OAuth flow:

```text
Application → eBay authorization → seller consent → callback → code exchange
→ access + refresh token → secure refresh-token storage → automatic refresh
```

Seller defaults required before publication:

```text
Payment policy
Fulfillment policy
Return policy
Inventory location
```

Target marketplace: `EBAY_CA`.

---

# 18. Image / Inventory / Offer / Publish Flow

```text
Local images → human review → Media API → eBay image URLs
→ createOrReplaceInventoryItem → createOffer → EBAY_STAGED
→ final confirmation → publishOffer → listing ID/URL
```

Publishing must remain separate and explicitly confirmed.

---

# 19. Security + Logging

HTTPS and application login are mandatory. No public registration. Secrets stay outside Git. CSRF protection, secure cookies, upload validation, generated filenames, max upload size, and production debug-off are required.

Log workflow events but never secrets, access/refresh tokens, passwords, or authorization headers.

---

# 20. Git / Build Discipline

- Work on one phase at a time.
- Every phase: implementation, tests, docs, manual verification, clean commit.
- Never hard-code secrets or commit `.env`.
- Use Sandbox until explicitly moving to Production.
- Never auto-publish AI-generated listings.
- Preserve manual edits.
- Stop on blockers rather than inventing API behavior.

The authoritative execution checklist is [`MASTER_LIST.md`](MASTER_LIST.md).

---

# 21. Playwright Fallback

Do not build Playwright alongside the API integration. Only use it if a concrete API limitation blocks a required workflow. Isolate it under `services/browser/ebay_playwright.py` and make it consume the same internal Listing model so upstream AI/taxonomy/pricing/review logic remains unchanged.

---

# 22. Final MVP Definition

The MVP is complete only when the full controlled pipeline works:

```text
PRODUCT PHOTOS
→ AI PRODUCT ANALYSIS
→ EBAY CATEGORY
→ REQUIRED ITEM SPECIFICS
→ ACTIVE MARKET COMPARABLES
→ PRICE RECOMMENDATION
→ TITLE + DESCRIPTION
→ HUMAN REVIEW
→ VALIDATION
→ APPROVAL
→ EBAY IMAGE UPLOAD
→ INVENTORY ITEM
→ OFFER
→ FINAL HUMAN CONFIRMATION
→ PUBLISH
→ EBAY LISTING ID
```

For the detailed phase-by-phase checklist and live completion state, use [`MASTER_LIST.md`](MASTER_LIST.md).