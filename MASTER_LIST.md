# eBayBay — Master List

**Status:** ACTIVE SOURCE OF TRUTH  
**Marketplace:** eBay Canada (`EBAY_CA`)  
**Environment:** Sandbox until Phase 14  
**Deployment:** Hostinger VPS, `/opt/docker/ebaybay`  
**Repository:** `jenozu/ebaybay`  
**Public OAuth host:** `https://ebaybay.andel-vps.space`

> This file is the authoritative build roadmap. A task is complete only when it has actually been implemented and verified. Planning, discussion, or partially working experiments do **not** count as completion.

## Checklist rules

- `[ ]` = not complete.
- `[x]` = implemented and verified.
- Do not mark a whole phase complete unless its Definition of Done passes.
- Work on one phase at a time unless a documented prerequisite must be completed out of order.
- Every phase ends with relevant tests, documentation updates, and a Git commit.
- Never commit `.env`, Client Secrets, access tokens, refresh tokens, or `data/token.json`.
- Never publish a real listing until Phase 14 explicitly moves the project to Production.
- AI-generated listings always require human review and explicit publish confirmation.

---

# Current reality — September 4, 2026

We intentionally completed the difficult eBay Sandbox/OAuth foundation **before** building the main listing application. Therefore Phase 3 is largely complete and Phase 8 has substantial prerequisite work complete even though Phases 1–7 have not been built yet.

## Verified pre-work already completed

- [x] GitHub repository `jenozu/ebaybay` exists.
- [x] Hostinger project directory `/opt/docker/ebaybay` exists.
- [x] Dockerized Flask/Gunicorn callback service runs on the VPS.
- [x] DNS/subdomain `ebaybay.andel-vps.space` points to the VPS.
- [x] HTTPS works through the existing reverse-proxy/TLS setup.
- [x] Sandbox eBay Developer keyset created.
- [x] Sandbox seller test user created.
- [x] Sandbox RuName configured.
- [x] OAuth scopes `sell.inventory` and `sell.account` authorized.
- [x] OAuth callback receives authorization codes.
- [x] Callback automatically exchanges a fresh code for access + refresh tokens.
- [x] Tokens are stored in the persistent `/app/data` volume rather than printed by the app.
- [x] Refresh-token grant was tested successfully.
- [x] Authenticated Inventory API smoke test returned HTTP 200 from `/sell/inventory/v1/getVersion`.
- [x] Repeatable OAuth instructions documented in `setup.md`.

## Not built yet

- [ ] Main draft/listing application.
- [ ] Database/models/migrations.
- [ ] Login UI.
- [ ] Photo upload workflow.
- [ ] AI product analysis.
- [ ] Taxonomy/category integration.
- [ ] Item-specific mapping.
- [ ] Active comparable search.
- [ ] Pricing engine.
- [ ] Listing writer.
- [ ] Review/edit UI.
- [ ] Validation/approval workflow.
- [ ] Seller policy/location settings UI.
- [ ] eBay Media API image upload.
- [ ] Inventory Item staging.
- [ ] Offer staging.
- [ ] Publish workflow.
- [ ] Production deployment.

---

# PHASE 0 — Project Initialization

## Goal

Create an isolated, reproducible project and put the actual source code under Git control.

## Tasks

- [x] Create GitHub repository `jenozu/ebaybay`.
- [x] Create VPS project directory `/opt/docker/ebaybay`.
- [x] Establish Python 3.12 + Flask + Gunicorn baseline.
- [x] Add `.gitignore` protecting secrets/tokens.
- [x] Add `.dockerignore` to Git.
- [x] Add `.env.example` containing variable names/placeholders only.
- [x] Add `README.md`.
- [x] Add repeatable OAuth `setup.md`.
- [x] Add `PRD.md` design reference.
- [x] Add `MASTER_LIST.md` as source-of-truth roadmap.
- [x] Add application source (`app/` package + `wsgi.py`) to Git.
- [x] Add current `requirements.txt` to Git.
- [x] Add current `Dockerfile` to Git.
- [x] Add current `docker-compose.yml` to Git with no secrets.
- [x] Add persistent `data/.gitkeep` and `uploads/.gitkeep` placeholders.
- [ ] Add `/health` route returning `{"status":"ok"}`.
- [x] Verify Docker container starts successfully on the VPS.
- [x] Verify Docker restart policy is configured.
- [ ] Verify repo clone/pull workflow on VPS so GitHub becomes the code source of truth instead of manual file edits.
- [ ] Run Phase 0 smoke test after pulling repo code onto VPS.
- [ ] Commit final Phase 0 completion state.

## Definition of Done

```text
git pull
docker compose up -d --build
GET /health → HTTP 200 {"status":"ok"}
```

and the VPS application source matches `main` in GitHub with no secrets committed.

---

# PHASE 1 — Core Draft Application

## Goal

Build a useful local listing/draft application before adding AI.

**Phase status:** COMPLETE — certified by automated tests, OAuth regression coverage, and migration reproduction.

## Application foundation

- [x] Refactor to Flask application factory.
- [x] Create `app/` package structure.
- [x] Add configuration module.
- [x] Configure SQLAlchemy.
- [x] Configure Alembic migrations.
- [x] Set SQLite database path `/app/data/app.db`.
- [x] Ensure DB persists through Docker restarts.

## Data models

- [x] Create `Listing` model.
- [x] Create `ListingImage` model.
- [x] Create `ListingAspect` model.
- [x] Create `ComparableListing` model.
- [x] Create `eBayConnection` model or equivalent secure connection storage abstraction.
- [x] Implement explicit listing state machine.
- [x] Add initial migration.

## Authentication

- [x] Add private single-user login.
- [x] Store password securely as a hash.
- [x] Protect listing/settings routes.
- [x] Configure secure session cookies.
- [x] Add CSRF protection.
- [x] No public registration.

## Draft workflow

- [x] Build dashboard.
- [x] Build New Listing page.
- [x] Accept multiple image uploads.
- [x] Validate MIME type and extension.
- [x] Generate safe filenames.
- [x] Configure maximum upload size.
- [x] Persist uploaded files in `/app/uploads`.
- [x] Add optional seller notes.
- [x] Generate internal unique SKU.
- [x] Save draft.
- [x] Reopen draft.
- [x] Edit draft.
- [x] Archive/delete draft safely.
- [x] Build listing detail page.
- [x] Display listing status.

## Tests

- [x] Test login/auth protection.
- [x] Test draft creation.
- [x] Test image upload validation.
- [x] Test draft persistence after restart.
- [x] Test edit/reopen flow.

## Definition of Done

```text
login
→ create draft
→ upload photos
→ enter notes
→ save
→ reopen
→ edit
```

works without AI or eBay APIs.

---

# PHASE 2 — AI Product Analysis

## Goal

Turn photos + seller notes into structured, editable product information without inventing facts.

**Phase status:** COMPLETE — certified by automated provider/schema/workflow tests and reproducible migrations.

## Provider architecture

- [x] Create AI provider interface.
- [x] Add provider configuration through `.env`.
- [x] Keep vendor-specific code behind provider abstraction.
- [x] Add model configuration.

## Structured analysis

- [x] Define Pydantic/structured JSON schema.
- [x] Include product name.
- [x] Include brand.
- [x] Include model.
- [x] Include MPN.
- [x] Include GTIN when genuinely visible/known.
- [x] Include condition suggestion.
- [x] Include condition confidence.
- [x] Include visible observations.
- [x] Include visible text.
- [x] Include search terms.
- [x] Include detected attributes.
- [x] Include uncertain fields.
- [x] Include overall confidence.

## Prompting rules

- [x] Do not infer unseen specifications.
- [x] Never invent MPNs/model numbers.
- [x] Distinguish visible text from inference.
- [x] Use `null` for unknown values.
- [x] Flag uncertainty.
- [x] Describe visible damage.
- [x] Never call an item new solely because it looks clean.
- [x] Seller notes override visual guesses about known facts.

## Workflow

- [x] Send multiple photos in one analysis.
- [x] Include seller notes.
- [x] Parse/validate structured response.
- [x] Handle malformed AI output.
- [x] Save raw AI JSON for debugging/audit.
- [x] Populate editable draft fields.
- [x] Display confidence.
- [x] Display uncertain fields.
- [x] Add Regenerate Analysis action.
- [x] Preserve user edits when regenerating unless explicitly replaced.

## Tests

- [x] Add mock AI fixtures.
- [x] Test valid response parsing.
- [x] Test invalid JSON handling.
- [x] Test null/uncertain fields.
- [x] Test seller-note precedence.

## Definition of Done

Photos + notes produce editable:

```text
brand
product name
model
MPN
condition suggestion
visible text
attributes
search terms
confidence / uncertainty
```

---

# PHASE 3 — eBay Developer + Sandbox Foundation

## Goal

Prove the app can authenticate safely against eBay Sandbox.

## Developer account / keyset

- [x] Create/verify eBay Developer account.
- [x] Create Sandbox application keyset.
- [x] Obtain Sandbox Client ID.
- [x] Obtain Sandbox Client Secret / Cert ID.
- [x] Identify Dev ID.
- [x] Keep Client Secret out of Git/screenshots going forward.

## Sandbox seller

- [x] Create Sandbox seller test account.
- [x] Confirm seller can authorize the application.
- [ ] Create separate Sandbox buyer account for eventual end-to-end transaction tests.

## Redirect / hosting

- [x] Create `ebaybay.andel-vps.space` DNS record.
- [x] Verify DNS resolves to VPS.
- [x] Configure HTTPS callback host.
- [x] Create/configure Sandbox RuName.
- [x] Configure Privacy Policy URL.
- [x] Configure Auth Accepted URL.
- [x] Configure Auth Declined URL.

## Credentials / scopes

- [x] Store credentials in VPS `.env`.
- [x] Exclude `.env` from Git.
- [x] Request `sell.inventory` scope.
- [x] Request `sell.account` scope.
- [x] Use `prompt=login` in working Sandbox authorization URL.
- [x] Confirm exact RuName is used as OAuth `redirect_uri`.

## Connectivity proof

- [x] Exchange authorization code successfully.
- [x] Receive access token.
- [x] Receive refresh token.
- [x] Test refresh-token grant.
- [x] Call Inventory API `getVersion` with User access token.
- [x] Confirm HTTP 200 response.
- [ ] Save a reusable `scripts/ebay_sandbox_test.py` smoke-test script in Git.
- [ ] Add safe config checker that never prints secrets.

## Definition of Done

**Functionally achieved.** eBay Sandbox authentication and an authenticated Inventory API call have been proven. Remaining unchecked items are repository hardening/support tooling, not blockers for moving back to Phase 0/1.

---

# PHASE 4 — Taxonomy + Item Specifics

## Goal

Use official eBay category metadata instead of AI guesses.

**Phase status:** COMPLETE — certified by deterministic Taxonomy mocks, full regression tests, and fresh-database migration reproduction.

## Tasks

- [x] Create `app/services/ebay/taxonomy.py`.
- [x] Fetch marketplace category-tree ID for `EBAY_CA`.
- [x] Cache stable tree metadata where sensible.
- [x] Implement category suggestions from product keywords/search terms.
- [x] Pass AI-derived search terms.
- [x] Display top category candidates.
- [x] Select a sensible default candidate.
- [x] Allow manual category override.
- [x] Store category ID.
- [x] Store category name.
- [x] Store category path.
- [x] Fetch category aspects.
- [x] Identify required aspects.
- [x] Identify recommended aspects.
- [x] Map AI attributes into eBay aspect names.
- [x] Flag required missing values prominently.
- [x] Persist ListingAspect records.
- [x] Add Taxonomy mocks/tests.

## Completion evidence

- Full suite: 33 tests passed, including Phase 1 draft, Phase 2 AI, and OAuth regression coverage.
- Fresh-database migration through `0003_phase4_taxonomy`: PASS.
- Taxonomy HTTP behavior is covered with deterministic mocks; no live API or credentials are required by automated tests.

## Definition of Done

The app displays selected eBay category, required/recommended item specifics, and missing required values for a draft.

---

# PHASE 5 — Active Comparable Search + Pricing

## Goal

Provide transparent market context and an explainable price recommendation.

**Phase status:** COMPLETE — certified by deterministic Browse mocks, scoring/pricing tests, full regressions, and fresh-database migration reproduction.

## Comparable search

- [x] Create `app/services/ebay/browse.py`.
- [x] Generate deterministic search terms.
- [x] Search exact MPN first.
- [x] Search brand + MPN.
- [x] Search brand + model.
- [x] Fall back to broader product terms.
- [x] Retrieve current active/purchasable listings.
- [x] Normalize currency.
- [x] Capture shipping cost where available.
- [x] Store comparable records.

## Similarity scoring

- [x] Exact MPN weighting.
- [x] Brand weighting.
- [x] Model weighting.
- [x] Condition weighting.
- [x] Category weighting.
- [x] Title-token overlap.
- [x] Remove obvious weak matches.
- [x] Keep/display strongest comparables.
- [x] Label all results **Active Comparables** (never sold comps).

## Pricing engine

- [x] Calculate comparable range.
- [x] Calculate comparable median.
- [x] Calculate quick-sale target.
- [x] Calculate recommended target.
- [x] Calculate high target.
- [x] Calculate pricing confidence.
- [x] Explain why confidence is high/medium/low.
- [x] Default final price to recommendation only when user has not manually overridden it.
- [x] Preserve manual final-price edits.
- [x] Add pricing/scoring tests.

## Completion evidence

- Full suite: 47 tests passed, including Phase 1–4 and OAuth regression coverage.
- Fresh-database migration through `0004_phase5_pricing`: PASS.
- Deterministic Browse mocks cover query priority/fallback, active response normalization, shipping, currency handling, persistence, and provider errors.
- Deterministic scoring/pricing tests cover weighted relevance, weak-match filtering, strongest-result limits, range/median/targets, confidence explanations, and manual-price preservation.

## Definition of Done

Review UI displays active comps, range, median, recommended price, alternative targets, and confidence.

---

# PHASE 6 — Listing Writer

## Goal

Generate factual, eBay-ready copy from validated product/category information.

## Tasks

- [ ] Add title generator.
- [ ] Enforce current eBay title-length limit.
- [ ] Prefer brand + MPN/model + product noun when supported.
- [ ] Avoid keyword stuffing.
- [ ] Add description generator.
- [ ] Use consistent description template.
- [ ] Add condition-description generator.
- [ ] Use seller notes as factual context.
- [ ] Use Taxonomy aspects as factual context.
- [ ] Never invent compatibility/specs.
- [ ] Save generated copy.
- [ ] Add Regenerate Title.
- [ ] Add Regenerate Description.
- [ ] Preserve manual edits.
- [ ] Add tests for factual/length constraints.

## Definition of Done

The review page contains a complete, editable listing draft with title, description, condition and specifics.

---

# PHASE 7 — Internal Validation + Human Approval

## Goal

Prevent broken or incomplete drafts from reaching eBay staging.

## Local validation

- [ ] Require at least one image.
- [ ] Require title.
- [ ] Require condition.
- [ ] Require quantity > 0.
- [ ] Require final price > 0.
- [ ] Require category.
- [ ] Require unique SKU.

## eBay metadata validation

- [ ] Validate mandatory category aspects.
- [ ] Validate selected payment policy.
- [ ] Validate selected fulfillment policy.
- [ ] Validate selected return policy.
- [ ] Validate inventory location.
- [ ] Validate marketplace.
- [ ] Validate listing format.

## Logical validation

- [ ] Validate title length.
- [ ] Validate price precision.
- [ ] Validate condition/category compatibility where applicable.
- [ ] Validate image status before staging.
- [ ] Validate OAuth/eBay connection usable.
- [ ] Return structured field-specific errors.

## Approval workflow

- [ ] Add grouped validation errors to UI.
- [ ] Add Approve Listing action.
- [ ] Only valid listing can become `READY`.
- [ ] Prevent AI auto-overwrite after approval.
- [ ] Allow Return to Draft.
- [ ] Add state-transition tests.

## Definition of Done

Only a valid, explicitly approved listing can reach `READY`.

---

# PHASE 8 — eBay OAuth User Connection

## Goal

Integrate the proven OAuth foundation into the actual application as a maintainable seller connection feature.

## Already proven outside main app

- [x] Working Sandbox authorization URL.
- [x] HTTPS callback route works.
- [x] Authorization-code exchange works.
- [x] Access token received.
- [x] Refresh token received.
- [x] Refresh-token grant works.
- [x] Authenticated Inventory API call works.
- [x] Persistent token volume works.

## Main-app integration still required

- [ ] Build Settings / Connect eBay page.
- [ ] Move OAuth logic into `app/services/ebay/oauth.py`.
- [ ] Generate state/CSRF value and verify it on callback.
- [ ] Store connection metadata in application database.
- [ ] Encrypt refresh token at rest where practical.
- [ ] Track access-token expiration.
- [ ] Implement reusable `get_access_token()` helper.
- [ ] Automatically refresh before/after expiry as appropriate.
- [ ] Persist renewed token metadata safely.
- [ ] Add Connected / Disconnected UI state.
- [ ] Display marketplace `EBAY_CA`.
- [ ] Display environment `Sandbox`.
- [ ] Add disconnect/reconnect.
- [ ] Handle revoked authorization.
- [ ] Ensure no tokens enter application logs/error pages.
- [ ] Add OAuth mocks/tests.
- [ ] Add Sandbox integration test through main app.

## Definition of Done

Settings displays:

```text
eBay: Connected
Marketplace: EBAY_CA
Environment: Sandbox
```

and all seller API clients obtain/refresh tokens through the shared OAuth service automatically.

---

# PHASE 9 — Seller Policies + Inventory Location

## Goal

Configure reusable seller defaults once rather than per listing.

## Tasks

- [ ] Create `app/services/ebay/account.py`.
- [ ] Retrieve payment policies.
- [ ] Retrieve fulfillment policies.
- [ ] Retrieve return policies.
- [ ] Retrieve inventory locations.
- [ ] Build Settings dropdowns.
- [ ] Store selected default payment policy ID.
- [ ] Store selected default fulfillment policy ID.
- [ ] Store selected default return policy ID.
- [ ] Store selected merchant location key.
- [ ] Lock/confirm marketplace `EBAY_CA` for MVP.
- [ ] Validate missing defaults before staging.
- [ ] Test selected IDs in Sandbox.
- [ ] Optionally add location creation later if retrieval alone is insufficient.

## Definition of Done

The app can build an offer using saved policy/location defaults without asking the seller on every listing.

---

# PHASE 10 — eBay Image Upload

## Goal

Move approved local listing images to eBay and persist returned image resources.

## Tasks

- [ ] Confirm exact Media API scope/requirements from current eBay docs before implementation.
- [ ] Create `app/services/ebay/media.py`.
- [ ] Upload approved local images.
- [ ] Capture eBay image/resource ID.
- [ ] Capture EPS/eBay-hosted image URL.
- [ ] Store both on ListingImage.
- [ ] Preserve image order.
- [ ] Show upload status.
- [ ] Retry transient errors safely.
- [ ] Make retry idempotent/avoid duplicate upload where possible.
- [ ] Add mocked tests.
- [ ] Add Sandbox integration test.

## Definition of Done

Approved local images have usable eBay-hosted image URLs stored on the draft.

---

# PHASE 11 — Inventory Item Staging

## Goal

Create/update the eBay Inventory Item without publishing it.

## Tasks

- [ ] Create `app/services/ebay/inventory.py`.
- [ ] Map Listing → Inventory Item payload.
- [ ] Send SKU.
- [ ] Send condition.
- [ ] Send aspects.
- [ ] Send product data.
- [ ] Send eBay image URLs.
- [ ] Send quantity where appropriate.
- [ ] Call `createOrReplaceInventoryItem`.
- [ ] Store sync result/status.
- [ ] Handle eBay validation errors cleanly.
- [ ] Make repeated staging idempotent.
- [ ] Add mocked tests.
- [ ] Add Sandbox integration test.

## Definition of Done

A `READY` local draft can be staged as an eBay Inventory Item without becoming live.

---

# PHASE 12 — Offer Staging

## Goal

Create the unpublished marketplace Offer tied to the Inventory Item.

## Tasks

- [ ] Build Offer payload.
- [ ] Add SKU.
- [ ] Add category ID.
- [ ] Add marketplace `EBAY_CA`.
- [ ] Add quantity.
- [ ] Add price/currency.
- [ ] Add fixed-price listing format.
- [ ] Add listing duration.
- [ ] Add payment policy ID.
- [ ] Add fulfillment policy ID.
- [ ] Add return policy ID.
- [ ] Add merchant location key.
- [ ] Call Create Offer.
- [ ] Store `offer_id`.
- [ ] Set internal state `EBAY_STAGED`.
- [ ] Surface staging errors clearly.
- [ ] Prevent duplicate/conflicting offers on retry.
- [ ] Add mocked tests.
- [ ] Add Sandbox integration test.

## Definition of Done

The app stores a valid unpublished Offer ID and the listing is `EBAY_STAGED`.

---

# PHASE 13 — Controlled Publish Workflow

## Goal

Publish only after explicit final human confirmation.

## Tasks

- [ ] Build final review panel.
- [ ] Display title, price, quantity, category and key specifics.
- [ ] Add visually distinct Publish action.
- [ ] Require explicit confirmation.
- [ ] Implement `publish_offer(offer_id)`.
- [ ] Store eBay listing ID.
- [ ] Store publish timestamp.
- [ ] Store listing URL when available.
- [ ] Set state `PUBLISHED`.
- [ ] Prevent accidental double publish.
- [ ] Handle publish failure without losing local draft.
- [ ] Add success screen.
- [ ] Add mocked tests.
- [ ] Add Sandbox end-to-end publish test.

## Definition of Done

A draft can go from photos → review → staged offer → explicit publish → successful Sandbox listing ID.

---

# PHASE 14 — Production Readiness

## Goal

Safely connect a real seller account and intentionally publish one low-risk real listing.

## eBay production

- [ ] Obtain Production eBay keyset.
- [ ] Configure Production RuName.
- [ ] Configure Production callback/privacy/declined URLs.
- [ ] Set environment switching cleanly (`sandbox` vs `production`).
- [ ] Connect real seller account.
- [ ] Retrieve real policies.
- [ ] Verify real inventory location.
- [ ] Verify `EBAY_CA`.

## App hardening

- [ ] Production login enabled.
- [ ] HTTPS verified.
- [ ] Production debug disabled.
- [ ] Gunicorn configured.
- [ ] Structured logging verified.
- [ ] Secrets absent from logs.
- [ ] CSRF/session security verified.
- [ ] Database backup script.
- [ ] Upload cleanup policy.
- [ ] Docker restart after VPS reboot verified.
- [ ] Restore-from-backup procedure documented/tested.

## Real smoke test

- [ ] Choose one low-risk item.
- [ ] Generate draft.
- [ ] Review all fields manually.
- [ ] Validate.
- [ ] Stage.
- [ ] Explicitly confirm publish.
- [ ] Publish successfully.
- [ ] Store listing ID/URL.
- [ ] Verify listing on eBay Canada.

## Definition of Done

One real listing is generated, reviewed, intentionally published, and recorded successfully with production safeguards active.

---

# MASTER MVP ACCEPTANCE TEST

The project is not complete until every item below passes in one controlled workflow.

- [ ] Open app.
- [ ] Log in.
- [ ] Click New Listing.
- [ ] Upload at least 3 images.
- [ ] Add seller notes.
- [ ] Click Analyze.
- [ ] AI returns structured product data.
- [ ] App suggests eBay category.
- [ ] App retrieves required aspects.
- [ ] App searches active comparables.
- [ ] App recommends price.
- [ ] App generates title.
- [ ] App generates description.
- [ ] User edits a generated field.
- [ ] Manual edit persists.
- [ ] Validator detects missing required data.
- [ ] User fills missing data.
- [ ] Listing passes validation.
- [ ] User approves.
- [ ] Images upload to eBay.
- [ ] Inventory Item is staged.
- [ ] Offer is staged.
- [ ] App displays final publish confirmation.
- [ ] User explicitly clicks Publish.
- [ ] eBay returns listing ID.
- [ ] App displays Published.
- [ ] Refreshing page does not duplicate listing.
- [ ] Published listing remains recorded in database.

---

# Recommended execution order from today

Because Sandbox/OAuth was deliberately proven first, return to the normal build order now:

```text
NOW → Finish Phase 0 (put baseline code + config under Git)
          ↓
Phase 1 — local drafts/photos/login/database
          ↓
Phase 2 — AI product analysis
          ↓
Phase 4 — Taxonomy + item specifics
          ↓
Phase 5 — active comps + pricing
          ↓
Phase 6 — listing writer
          ↓
Phase 7 — validation + approval
          ↓
Phase 8 — integrate proven OAuth into main app
          ↓
Phase 9 — seller policies + location
          ↓
Phase 10 — image upload
          ↓
Phase 11 — Inventory Item
          ↓
Phase 12 — Offer
          ↓
Phase 13 — Sandbox publish
          ↓
Phase 14 — Production
```

Phase 3 does not need to be repeated; its verified OAuth/Sandbox foundation should be reused. Phase 8 is **not** considered complete until that proven foundation is integrated into the main app's Settings/connection architecture.

---

# Multi-account note (future)

The MVP remains single-seller, but the architecture should not hard-code a single eBay identity into business logic. The eventual three-account design should create one eBayConnection/account profile per seller, each with its own refresh token, policy IDs, merchant location key and account-specific defaults. Do **not** build multi-account UI during the MVP unless required; just avoid architecture that would make it impossible later.

---

# Agent / LLM rules

Any coding agent working on this repo must:

1. Read `MASTER_LIST.md`, `PRD.md`, `setup.md`, and current repository state first.
2. Work only on the assigned current phase.
3. Never mark a task `[x]` merely because code was drafted; it must be tested/verified.
4. Keep the app runnable after every phase.
5. Add tests for important new behavior.
6. Run relevant tests before declaring success.
7. Never hard-code or commit credentials/tokens.
8. Never use Production until Phase 14 is explicitly authorized.
9. Never auto-publish an AI-generated listing.
10. Preserve manual user edits.
11. Update `MASTER_LIST.md` immediately when a task is completed.
12. Update docs when architecture/setup changes.
13. Commit after each coherent completed phase/milestone.
14. Stop and report blockers instead of inventing eBay behavior.
