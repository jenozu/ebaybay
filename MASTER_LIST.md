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

**Phase status:** COMPLETE — certified by deterministic evidence-grounded writer tests, full regressions, and fresh-database migration reproduction.

## Tasks

- [x] Add title generator.
- [x] Enforce current eBay title-length limit.
- [x] Prefer brand + MPN/model + product noun when supported.
- [x] Avoid keyword stuffing.
- [x] Add description generator.
- [x] Use consistent description template.
- [x] Add condition-description generator.
- [x] Use seller notes as factual context.
- [x] Use Taxonomy aspects as factual context.
- [x] Never invent compatibility/specs.
- [x] Save generated copy.
- [x] Add Regenerate Title.
- [x] Add Regenerate Description.
- [x] Preserve manual edits.
- [x] Add tests for factual/length constraints.

## Completion evidence

- Full suite: 59 tests passed, including Phase 1–5 and OAuth regression coverage.
- Fresh-database migration through `0005_phase6_writer`: PASS.
- Deterministic writer tests cover identifiers, title limit/truncation, Unicode, missing fields, duplicate-token prevention, escaped HTML, taxonomy aspects, seller notes, condition copy, and comparable-text exclusion.
- Route tests cover generated-copy persistence, editing, protected endpoints, manual-copy preservation, explicit replacement, and title-length enforcement.

## Definition of Done

The review page contains a complete, editable listing draft with title, description, condition and specifics.

---

# PHASE 7 — Internal Validation + Human Approval

## Goal

Prevent broken or incomplete drafts from reaching eBay staging.

**Phase status:** COMPLETE — certified by deterministic validation/approval tests and full regression coverage. No schema migration was required.

## Local validation

- [x] Require at least one image.
- [x] Require title.
- [x] Require condition.
- [x] Require quantity > 0.
- [x] Require final price > 0.
- [x] Require category.
- [x] Require unique SKU.

## eBay metadata validation

- [x] Validate mandatory category aspects.
- [x] Validate selected payment policy.
- [x] Validate selected fulfillment policy.
- [x] Validate selected return policy.
- [x] Validate inventory location.
- [x] Validate marketplace.
- [x] Validate listing format.

## Logical validation

- [x] Validate title length.
- [x] Validate price precision.
- [x] Validate condition/category compatibility where applicable.
- [x] Validate image status before staging.
- [x] Validate OAuth/eBay connection usable.
- [x] Return structured field-specific errors.

## Approval workflow

- [x] Add grouped validation errors to UI.
- [x] Add Approve Listing action.
- [x] Only valid listing can become `READY`.
- [x] Prevent AI auto-overwrite after approval.
- [x] Allow Return to Draft.
- [x] Add state-transition tests.

## Completion evidence

- Full suite: 68 tests passed, including Phase 1–6 and OAuth regression coverage.
- Migration: no migration required; approval state is represented by the existing persisted `DRAFT`/`READY` listing status.
- Deterministic validation tests cover saved images, title, condition, quantity, price/precision, category, SKU, required aspects, seller policy/location/marketplace/format configuration, and local OAuth-token usability.
- Approval tests cover invalid rejection, explicit valid approval, protected routes, return-to-draft, material-edit invalidation, and blocking AI analysis while approved.
- Category-specific condition compatibility has no additional local rule in the stored eBay metadata; the validator enforces the selected condition and selected category and is reusable for later official compatibility metadata.

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

- [x] Build Settings / Connect eBay page.
- [x] Move OAuth logic into `app/services/ebay/oauth.py`.
- [x] Generate state/CSRF value and verify it on callback.
- [x] Store connection metadata in application database.
- [x] Encrypt refresh token at rest where practical.
- [x] Track access-token expiration.
- [x] Implement reusable `get_access_token()` helper.
- [x] Automatically refresh before/after expiry as appropriate.
- [x] Persist renewed token metadata safely.
- [x] Add Connected / Disconnected UI state.
- [x] Display marketplace `EBAY_CA`.
- [x] Display environment `Sandbox`.
- [x] Add disconnect/reconnect.
- [x] Handle revoked authorization.
- [x] Ensure no tokens enter application logs/error pages.
- [x] Add OAuth mocks/tests.
- [x] Add Sandbox integration test through main app.

## Definition of Done

Settings displays:

```text
eBay: Connected
Marketplace: EBAY_CA
Environment: Sandbox
```

and all seller API clients obtain/refresh tokens through the shared OAuth service automatically.

## Completion evidence

- Phase 8 certified locally with 75 passed, 1 opt-in Sandbox smoke test skipped.
- Migration `0006_phase8_oauth_connection.py` passes both the full fresh-database chain and upgrade from the Phase 7 revision.
- Deterministic tests cover OAuth state validation/reuse, encrypted token persistence, expiry refresh, revoked authorization, Settings connection controls, CSRF, and Taxonomy/Browse shared-token integration.
- The live Sandbox smoke test exercises the main application OAuth service when `RUN_EBAY_SANDBOX_INTEGRATION=1`; browser consent/reconnection and VPS deployment remain external verification.

---

# PHASE 9 — Seller Policies + Inventory Location

## Goal

Configure reusable seller defaults once rather than per listing.

## Tasks

- [x] Create `app/services/ebay/account.py`.
- [x] Retrieve payment policies.
- [x] Retrieve fulfillment policies.
- [x] Retrieve return policies.
- [x] Retrieve inventory locations.
- [x] Build Settings dropdowns.
- [x] Store selected default payment policy ID.
- [x] Store selected default fulfillment policy ID.
- [x] Store selected default return policy ID.
- [x] Store selected merchant location key.
- [x] Lock/confirm marketplace `EBAY_CA` for MVP.
- [x] Validate missing defaults before staging.
- [x] Test selected IDs in Sandbox.
- [ ] Optionally add location creation later if retrieval alone is insufficient.

## Definition of Done

The app can build an offer using saved policy/location defaults without asking the seller on every listing.

## Completion evidence

- Phase 9 certified locally with 79 passed and 2 opt-in Sandbox integration tests skipped.
- Migration `0007_phase9_seller_defaults.py` passes both upgrade from the Phase 8 revision and the full fresh-database migration chain.
- Deterministic Account/Inventory mocks cover normalized payment, fulfillment, and return policy retrieval, location pagination, disabled locations, safe errors, Settings persistence, stale selections, and Phase 7 validation.
- `sell.account` was added to the shared OAuth consent scopes; existing Sandbox authorization must be reconnected externally before Account API calls can succeed.
- The opt-in Sandbox test verifies retrieved policy/location resources and selected IDs through the shared OAuth service when `RUN_EBAY_SANDBOX_INTEGRATION=1`.

---

# PHASE 10 — eBay Image Upload

## Goal

Move approved local listing images to eBay and persist returned image resources.

## Tasks

- [x] Confirm exact Media API scope/requirements from current eBay docs before implementation.
- [x] Create `app/services/ebay/media.py`.
- [x] Upload approved local images.
- [x] Capture eBay image/resource ID.
- [x] Capture EPS/eBay-hosted image URL.
- [x] Store both on ListingImage.
- [x] Preserve image order.
- [x] Show upload status.
- [x] Retry transient errors safely.
- [x] Make retry idempotent/avoid duplicate upload where possible.
- [x] Add mocked tests.
- [x] Add Sandbox integration test.

## Definition of Done

Approved local images have usable eBay-hosted image URLs stored on the draft.

## Completion evidence

- Phase 10 certified locally with 83 passed and 3 opt-in Sandbox integration tests skipped.
- Migration `0008_phase10_media_upload.py` passes upgrade from the Phase 9 revision and the full fresh-database migration chain.
- Mocked Media API coverage verifies the documented Sandbox endpoint, shared OAuth token, binary MIME upload, returned image ID/URL persistence, bounded transient retry, non-transient failure, fingerprint idempotency, image ordering, approved-only UI/action, and CSRF/authentication regression coverage.
- The existing `sell.inventory` OAuth scope is sufficient for the Media image endpoint; no new consent scope was added.
- The opt-in Sandbox Media test uses the main application OAuth and Media services when `RUN_EBAY_SANDBOX_INTEGRATION=1` and `EBAY_SANDBOX_MEDIA_TEST_IMAGE` are set.

---

# PHASE 11 — Inventory Item Staging

## Goal

Create/update the eBay Inventory Item without publishing it.

## Tasks

- [x] Create `app/services/ebay/inventory.py`.
- [x] Map Listing → Inventory Item payload.
- [x] Send SKU.
- [x] Send condition.
- [x] Send aspects.
- [x] Send product data.
- [x] Send eBay image URLs.
- [x] Send quantity where appropriate.
- [x] Call `createOrReplaceInventoryItem`.
- [x] Store sync result/status.
- [x] Handle eBay validation errors cleanly.
- [x] Make repeated staging idempotent.
- [x] Add mocked tests.
- [x] Add Sandbox integration test.

## Definition of Done

A `READY` local draft can be staged as an eBay Inventory Item without becoming live.

### Completion evidence

- Phase 11 certified locally with 87 passed and 4 opt-in Sandbox integration tests skipped. Deterministic coverage verifies factual payload mapping, shared OAuth token use, Sandbox endpoint selection, image order, safe API failures, idempotent repeat staging, protected UI flow, and retained `READY` status.
- Migration `0009_phase11_inventory_staging` adds durable local Inventory Item staging status and payload fingerprint state.
- The opt-in Sandbox check uses the main application OAuth and Inventory services when `RUN_EBAY_SANDBOX_INTEGRATION=1` and a disposable `EBAY_SANDBOX_MEDIA_URL` are supplied.

---

# PHASE 12 — Offer Staging

## Goal

Create the unpublished marketplace Offer tied to the Inventory Item.

## Tasks

- [x] Build Offer payload.
- [x] Add SKU.
- [x] Add category ID.
- [x] Add marketplace `EBAY_CA`.
- [x] Add quantity.
- [x] Add price/currency.
- [x] Add fixed-price listing format.
- [x] Add listing duration.
- [x] Add payment policy ID.
- [x] Add fulfillment policy ID.
- [x] Add return policy ID.
- [x] Add merchant location key.
- [x] Call Create Offer.
- [x] Store `offer_id`.
- [x] Set internal state `EBAY_STAGED`.
- [x] Surface staging errors clearly.
- [x] Prevent duplicate/conflicting offers on retry.
- [x] Add mocked tests.
- [x] Add Sandbox integration test.

## Definition of Done

The app stores a valid unpublished Offer ID and the listing is `EBAY_STAGED`.

### Completion evidence

- Phase 12 certified locally with 91 passed and 5 opt-in Sandbox integration tests skipped. Deterministic coverage verifies the exact unpublished Offer payload, seller-default reuse, shared OAuth token use, Sandbox endpoint, persisted offer ID/state, UI/auth protection, and duplicate/unknown-outcome handling.
- Migration `0010_phase12_offer_staging` was verified from the Phase 11 schema and through a fresh full migration chain.
- The opt-in Sandbox Offer test uses the main OAuth and Offer services when `RUN_EBAY_SANDBOX_INTEGRATION=1`; it requires a pre-staged Inventory Item, connected seller defaults, and `EBAY_SANDBOX_CATEGORY_ID`.

---

# PHASE 13 — Controlled Publish Workflow

## Goal

Publish only after explicit final human confirmation.

## Tasks

- [x] Build final review panel.
- [x] Display title, price, quantity, category and key specifics.
- [x] Add visually distinct Publish action.
- [x] Require explicit confirmation.
- [x] Implement `publish_offer(offer_id)`.
- [x] Store eBay listing ID.
- [x] Store publish timestamp.
- [x] Store listing URL when available.
- [x] Set state `PUBLISHED`.
- [x] Prevent accidental double publish.
- [x] Handle publish failure without losing local draft.
- [x] Add success screen.
- [x] Add mocked tests.
- [x] Add Sandbox end-to-end publish test.

## Definition of Done

A draft can go from photos → review → staged offer → explicit publish → successful Sandbox listing ID.

### Completion evidence

- Phase 13 certified locally with 94 passed and 6 opt-in Sandbox integration tests skipped. Deterministic coverage verifies final review display, exact confirmation enforcement, shared OAuth use, Sandbox publish endpoint, response persistence, double-publish protection, and safe failure/unknown-outcome handling.
- Migration `0011_phase13_publish_workflow` was verified from the Phase 12 schema and through a fresh full migration chain.
- The opt-in Sandbox publish check uses the main OAuth and Publish services when `RUN_EBAY_SANDBOX_INTEGRATION=1` and `EBAY_SANDBOX_OFFER_ID` identifies a disposable staged Sandbox offer.

---

# PHASE 14 — Production Readiness

## Goal

Safely connect a real seller account and intentionally publish one low-risk real listing.

## eBay production

- [ ] Obtain Production eBay keyset.
- [ ] Configure Production RuName.
- [ ] Configure Production callback/privacy/declined URLs.
- [x] Set environment switching cleanly (`sandbox` vs `production`).
- [ ] Connect real seller account.
- [ ] Retrieve real policies.
- [ ] Verify real inventory location.
- [ ] Verify `EBAY_CA`.

## App hardening

- [x] Production login enabled.
- [x] HTTPS verified.
- [x] Production debug disabled.
- [x] Gunicorn configured.
- [x] Structured logging verified.
- [x] Secrets absent from logs.
- [x] CSRF/session security verified.
- [x] Database backup script.
- [x] Upload cleanup policy.
- [ ] Docker restart after VPS reboot verified.
- [x] Restore-from-backup procedure documented/tested.

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

### Local readiness evidence (not Phase 14 completion)

- Local production guardrail coverage passes with 99 tests and 6 opt-in Sandbox integration tests skipped. Production startup fails closed without required credentials, encryption, secure sessions, `EBAY_CA`, and a non-default secret.
- Structured credential-redacting logs, Gunicorn stream logging, SQLite backup/restore tooling, and dry-run-first orphan-upload cleanup are implemented and tested. No schema migration was required.
- Remaining unchecked Phase 14 items require an actual Production eBay keyset/RuName, HTTPS-enabled VPS deployment, real seller authorization/policies/location, Docker restart verification, and an intentional low-risk real listing. They have not been claimed as complete.
- Public HTTPS was verified on 2026-09-05 for `/`, `/privacy`, and `/oauth/declined`. The public `/health` endpoint returned 404, so the VPS is serving an older application tree and still needs deployment from GitHub `main` before Production activation.

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
