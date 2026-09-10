# eBayBay — Master Build & Production Readiness List

**Status:** ACTIVE SOURCE OF TRUTH  
**Last reconciled:** 2026-09-10  
**Repository:** `jenozu/ebaybay`  
**Branch:** `main`  
**Marketplace:** eBay Canada (`EBAY_CA`)  
**Public host:** `https://ebaybay.andel-vps.space`  
**Deployment:** Hostinger VPS, `/opt/docker/ebaybay`

> This file is the authoritative project roadmap and completion record. GitHub `main` plus this file define the current project state. A task is complete only when it has been implemented, verified, documented here, committed, and pushed.

## Completion and Git discipline

- `[ ]` = incomplete, blocked, or not yet verified.
- `[x]` = implemented and verified.
- Do not mark a task complete because code was drafted or discussed.
- Do not mark a phase complete until its Definition of Done is satisfied.
- Every coherent completed task or phase must end with:
  1. relevant tests,
  2. `MASTER_LIST.md` reconciliation,
  3. a Git commit,
  4. push to `main`, and
  5. CI verification when CI applies.
- Do not leave completed work only on a VPS, local workstation, temporary branch, or uncommitted worktree.
- GitHub `main` is the application-code source of truth. The VPS should be deployed from `main`; avoid manual source edits on the VPS.
- Never commit `.env`, Client Secrets, access tokens, refresh tokens, encryption keys, passwords, or `data/token.json`.
- Never expose credentials or tokens in UI, logs, errors, tests, screenshots, or documentation.
- Production publishing always requires human review and explicit publish confirmation.
- Any coding agent must update this file immediately after completing a task whose status changes.

---

# CURRENT REALITY — September 10, 2026

The original roadmap text became stale while implementation continued. This section supersedes older assumptions about phases not being built.

## Current verified application state

- [x] Phases 1–13 are implemented in the main application.
- [x] Private login, CSRF, secure sessions, database persistence, and migrations are implemented.
- [x] Draft creation, image upload, seller notes, editing, and archive/delete workflow are implemented.
- [x] AI product analysis is implemented.
- [x] eBay Taxonomy/category and item-specific workflows are implemented.
- [x] Active comparable search and pricing recommendation are implemented.
- [x] Listing title/description/condition writing is implemented.
- [x] Internal validation and explicit human approval are implemented.
- [x] Shared eBay OAuth connection service is implemented.
- [x] Seller policy retrieval and saved defaults are implemented.
- [x] Inventory-location retrieval is implemented.
- [x] eBay Media image upload is implemented.
- [x] Inventory Item staging is implemented.
- [x] unpublished Offer staging is implemented.
- [x] controlled publish workflow is implemented.
- [x] `/health` exists in the current application and returns `{"status":"ok"}`.
- [x] Production-safe inventory-location creation is implemented in Settings.
- [x] Latest feature commit is on `main`: `fbf5ff74fc3347f5ec5346c4411e639422d08774` — `Add eBay inventory location creation`.
- [x] Latest CI for that commit passed: **102 passed, 6 opt-in Sandbox tests skipped**.
- [x] Fresh-database migration verification passed in CI.
- [x] Repository clean-tree verification passed in CI.

## Current active objective

**Phase 14 — Production Readiness** remains the active phase. The remaining work is primarily live Production/VPS verification and the first intentional low-risk real listing, not rebuilding Phases 1–13.

## Immediate next actions

- [ ] Deploy current GitHub `main` (including `fbf5ff74`) to the VPS.
- [ ] Confirm live `/health` returns HTTP 200 from the deployed current app.
- [ ] Open live Settings and verify the real Production seller connection.
- [ ] Create or verify a real eBay inventory location using the Settings feature.
- [ ] Refresh real eBay policies and inventory locations.
- [ ] Save real payment, fulfillment, return, and merchant-location defaults.
- [ ] Verify Docker restart after VPS reboot.
- [ ] Run one controlled real Production listing from draft through publish.
- [ ] Record the first Production listing ID/URL and final verification here.

---

# PHASE 0 — Project Initialization

## Goal

Keep the project reproducible and Git-controlled.

## Status

**FUNCTIONALLY COMPLETE; VPS source-of-truth deployment verification still belongs to Phase 14 operational work.**

## Verified

- [x] GitHub repository exists.
- [x] Flask application factory and Python/Gunicorn baseline exist.
- [x] `.gitignore` and `.dockerignore` protect local/secrets files.
- [x] `.env.example`, `README.md`, `setup.md`, `PRD.md`, and `MASTER_LIST.md` exist.
- [x] Application source is in Git.
- [x] Dockerfile and Compose configuration are in Git.
- [x] persistent data/uploads directories are supported.
- [x] `/health` route exists.
- [x] Docker restart policy is configured.

## Remaining operational verification

- [ ] Confirm the VPS is running the latest GitHub `main` rather than an older application tree.
- [ ] Confirm the repeatable `git pull` → Docker rebuild/restart deployment workflow on the VPS.

---

# PHASE 1 — Core Draft Application

**Status: COMPLETE**

- [x] Flask application factory and configuration.
- [x] SQLAlchemy + Alembic migrations.
- [x] persistent SQLite database.
- [x] Listing, ListingImage, ListingAspect, ComparableListing, and eBay connection persistence.
- [x] private single-user authentication.
- [x] password hashing.
- [x] secure session configuration.
- [x] CSRF protection.
- [x] no public registration.
- [x] dashboard and New Listing workflow.
- [x] multiple image uploads with validation and safe filenames.
- [x] seller notes and unique SKU generation.
- [x] save/reopen/edit/archive/delete workflows.
- [x] listing state/status display.
- [x] automated draft/auth/upload tests.

**Definition of Done:** local draft workflow works without requiring AI or eBay APIs.

---

# PHASE 2 — AI Product Analysis

**Status: COMPLETE**

- [x] provider abstraction and environment configuration.
- [x] structured product-analysis schema.
- [x] product/brand/model/MPN/GTIN handling.
- [x] condition suggestion/confidence.
- [x] visible observations/text and search terms.
- [x] detected attributes and uncertainty handling.
- [x] no invention of unseen facts or identifiers.
- [x] seller-note precedence.
- [x] structured-response validation and safe malformed-output handling.
- [x] raw analysis persistence for audit/debugging.
- [x] editable populated fields and regeneration flow.
- [x] manual-edit preservation.
- [x] mocked provider/schema/workflow tests.

**Definition of Done:** photos + notes produce structured, editable, evidence-grounded product information.

---

# PHASE 3 — eBay Developer + Sandbox Foundation

**Status: FUNCTIONALLY COMPLETE**

- [x] Sandbox application keyset established.
- [x] Sandbox seller authorization proven.
- [x] Sandbox RuName/callback configuration proven.
- [x] `sell.inventory` and `sell.account` scopes supported.
- [x] authorization-code exchange proven.
- [x] access + refresh token flow proven.
- [x] refresh-token grant proven.
- [x] authenticated Inventory API call proven.
- [x] credentials kept outside Git.

## Optional/non-blocking Sandbox work

- [ ] Separate Sandbox buyer account for transaction testing if eventually needed.

---

# PHASE 4 — Taxonomy + Item Specifics

**Status: COMPLETE**

- [x] eBay Taxonomy service.
- [x] `EBAY_CA` category tree handling.
- [x] category suggestions and manual override.
- [x] category ID/name/path persistence.
- [x] required/recommended aspect retrieval.
- [x] AI attribute → eBay aspect mapping.
- [x] missing-required-aspect validation.
- [x] deterministic mocked tests.

**Historical certification:** 33 tests passed at Phase 4 completion.

---

# PHASE 5 — Active Comparable Search + Pricing

**Status: COMPLETE**

- [x] Browse API service.
- [x] prioritized product-search term generation.
- [x] current active/purchasable comparable retrieval.
- [x] shipping/currency normalization.
- [x] comparable persistence.
- [x] similarity scoring.
- [x] weak-match filtering.
- [x] range/median/quick-sale/recommended/high pricing targets.
- [x] pricing confidence explanation.
- [x] manual final-price preservation.
- [x] mocked Browse/pricing tests.

**Historical certification:** 47 tests passed at Phase 5 completion.

---

# PHASE 6 — Listing Writer

**Status: COMPLETE**

- [x] title generator.
- [x] eBay title-length enforcement.
- [x] evidence-grounded keyword selection.
- [x] description generator.
- [x] condition-description generator.
- [x] seller notes and taxonomy aspects used as factual context.
- [x] compatibility/specification invention blocked.
- [x] generated-copy persistence.
- [x] regeneration controls.
- [x] manual-copy preservation.
- [x] deterministic writer tests.

**Historical certification:** 59 tests passed.  
**Completion commit:** `93726d00a062a2f9d22d7ef67742949aa891a1b2`.

---

# PHASE 7 — Internal Validation + Human Approval

**Status: COMPLETE**

- [x] image/title/condition/quantity/price/category/SKU validation.
- [x] mandatory aspect validation.
- [x] payment/fulfillment/return policy validation.
- [x] merchant-location validation.
- [x] marketplace/listing-format validation.
- [x] title length and price precision validation.
- [x] OAuth usability validation.
- [x] grouped field-specific UI errors.
- [x] explicit Approve Listing action.
- [x] only valid listings can become `READY`.
- [x] Return to Draft workflow.
- [x] approved-listing edit/AI overwrite protection.
- [x] state-transition tests.

**Historical certification:** 68 tests passed.  
**Completion commit:** `02ccbf22`.

---

# PHASE 8 — eBay OAuth User Connection

**Status: COMPLETE**

- [x] Settings / Connect eBay page.
- [x] reusable OAuth service.
- [x] callback state verification.
- [x] encrypted refresh-token persistence.
- [x] access-token expiration tracking.
- [x] reusable `get_access_token()`.
- [x] automatic refresh.
- [x] Connected / Disconnected UI state.
- [x] reconnect/disconnect controls.
- [x] safe revoked-authorization handling.
- [x] no token exposure in logs/error pages.
- [x] deterministic OAuth tests.
- [x] opt-in Sandbox integration coverage.

**Historical certification:** 75 passed, 1 opt-in Sandbox test skipped.  
**Completion commit:** `4b2c21ef`.

---

# PHASE 9 — Seller Policies + Inventory Location

**Status: COMPLETE**

## Seller defaults

- [x] `app/services/ebay/account.py`.
- [x] retrieve payment policies.
- [x] retrieve fulfillment policies.
- [x] retrieve return policies.
- [x] retrieve inventory locations with pagination.
- [x] Settings dropdowns.
- [x] save payment/fulfillment/return default IDs.
- [x] save default merchant location key.
- [x] `EBAY_CA` locked/validated for MVP.
- [x] stale/missing default validation before staging.

## Inventory-location creation — added 2026-09-10

- [x] Add `create_inventory_location()` to the existing eBay account/inventory service.
- [x] Use official Inventory API `POST /sell/inventory/v1/location/{merchantLocationKey}` endpoint.
- [x] Reuse the shared OAuth User access token.
- [x] Support merchant location key.
- [x] Support location name.
- [x] Support address line, city, state/province, postal code, and two-letter country code.
- [x] Default location type to `WAREHOUSE`.
- [x] Support enabled/disabled status.
- [x] Validate required input and reject unsafe/unsupported location types.
- [x] URL-encode merchant location keys.
- [x] Add authenticated Settings POST route.
- [x] Add CSRF-protected Settings form.
- [x] Refresh cached seller inventory locations automatically after successful creation.
- [x] Preserve cached payment/fulfillment/return policies during location-only refresh.
- [x] Newly created enabled location becomes immediately selectable as default merchant location.
- [x] Mock endpoint/payload/error/cache tests.
- [x] Route auth and CSRF coverage.
- [x] No changes to offer/publish logic.
- [x] No credentials/tokens exposed.

## Completion evidence

- Original Phase 9 certification: 79 passed, 2 opt-in Sandbox tests skipped.
- Inventory-location creation completion commit: `fbf5ff74fc3347f5ec5346c4411e639422d08774`.
- CI after inventory-location feature: **102 passed, 6 skipped**.
- Fresh-database migration chain: PASS.
- Clean-tree verification: PASS.

**Definition of Done:** the app can retrieve or create a usable eBay merchant location and can save all seller defaults required for offer staging.

---

# PHASE 10 — eBay Image Upload

**Status: COMPLETE**

- [x] eBay Media service.
- [x] approved local image upload.
- [x] eBay resource ID and hosted URL persistence.
- [x] image ordering.
- [x] upload status.
- [x] safe transient retry.
- [x] duplicate/idempotency handling.
- [x] mocked tests.
- [x] opt-in Sandbox integration coverage.

**Historical certification:** 83 passed, 3 skipped.

---

# PHASE 11 — Inventory Item Staging

**Status: COMPLETE**

- [x] Inventory API service.
- [x] Listing → Inventory Item payload mapping.
- [x] SKU/condition/aspects/product/image/quantity mapping.
- [x] `createOrReplaceInventoryItem`.
- [x] staging status persistence.
- [x] safe validation/API error handling.
- [x] idempotent retry behavior.
- [x] mocked tests.
- [x] opt-in Sandbox integration coverage.

**Historical certification:** 87 passed, 4 skipped.  
**Completion commit:** `cfcd880af9ce7014cc39b89e20b1c6892f9691df`.

---

# PHASE 12 — Offer Staging

**Status: COMPLETE**

- [x] Offer payload construction.
- [x] SKU/category/marketplace/quantity/price/currency mapping.
- [x] fixed-price format and listing duration.
- [x] payment/fulfillment/return policy IDs.
- [x] merchant location key.
- [x] Create Offer call.
- [x] offer ID persistence.
- [x] `EBAY_STAGED` state.
- [x] safe retry/duplicate handling.
- [x] mocked tests.
- [x] opt-in Sandbox integration coverage.

**Historical certification:** 91 passed, 5 skipped.  
**Completion commit:** `7e4092bc427253bc8b0f39b3cb6469a66f3ebaeb`.

---

# PHASE 13 — Controlled Publish Workflow

**Status: COMPLETE**

- [x] final review panel.
- [x] title/price/quantity/category/key-specific review.
- [x] visually distinct Publish action.
- [x] explicit confirmation requirement.
- [x] `publish_offer(offer_id)`.
- [x] listing ID, timestamp, and URL persistence.
- [x] `PUBLISHED` state.
- [x] double-publish protection.
- [x] safe failed/unknown-outcome handling.
- [x] success screen.
- [x] mocked tests.
- [x] opt-in Sandbox publish coverage.

**Historical certification:** 94 passed, 6 skipped.  
**Completion commit:** `38c16c5dd6bd9bbdbaad0ca1767cdeb4b9a21e9a`.

---

# PHASE 14 — Production Readiness

## Goal

Safely run the current application against the real seller account and intentionally publish one low-risk eBay Canada listing.

**Status: IN PROGRESS**

## Production configuration

The following external/account-level items must only be checked when positively verified against the current Production setup. Do not infer them merely from local test success.

- [ ] Production eBay keyset positively verified against the currently deployed app configuration.
- [ ] Production RuName positively verified.
- [ ] Production callback/privacy/declined URLs positively verified.
- [x] Environment switching (`sandbox` / `production`) implemented.
- [ ] Real seller OAuth connection verified in the current deployed app.
- [ ] Real payment policies retrieved in the current deployed app.
- [ ] Real fulfillment policies retrieved in the current deployed app.
- [ ] Real return policies retrieved in the current deployed app.
- [ ] Real inventory location created or retrieved in the current deployed app.
- [ ] Real seller defaults saved.
- [x] `EBAY_CA` application validation implemented.
- [ ] `EBAY_CA` confirmed in the live Production Settings flow.

## App hardening

- [x] Production login.
- [x] HTTPS public host verified previously.
- [x] Production debug disabled.
- [x] Gunicorn configured.
- [x] structured logging.
- [x] credential redaction / secrets absent from logs.
- [x] CSRF/session protections.
- [x] database backup tooling.
- [x] restore procedure documented/tested.
- [x] upload-cleanup policy.
- [x] `/health` route implemented in current `main`.
- [ ] Current `main` deployed to VPS and `/health` verified live.
- [ ] Docker auto-restart after an actual VPS reboot verified.

## Production inventory-location support

- [x] Settings can create a Production inventory location safely using existing OAuth.
- [x] successful creation refreshes cached seller locations.
- [x] enabled created locations are selectable as the default merchant location.
- [x] mocked behavior/security coverage passes.
- [ ] Feature deployed to VPS.
- [ ] Feature verified against the real Production seller account.

## First real smoke test

- [ ] Choose one low-risk item.
- [ ] Create/open draft.
- [ ] Upload images and notes.
- [ ] Analyze.
- [ ] Confirm category and required aspects.
- [ ] Review active comparables and final price.
- [ ] Generate/review title, description, and condition text.
- [ ] Resolve all validation issues.
- [ ] Approve listing.
- [ ] Upload images to eBay.
- [ ] Stage Inventory Item.
- [ ] Stage Offer.
- [ ] Review final publish panel.
- [ ] Explicitly confirm publish.
- [ ] Publish successfully.
- [ ] Persist eBay listing ID/URL.
- [ ] Verify the listing on eBay Canada.
- [ ] Record smoke-test evidence here.

## Latest readiness evidence

- Phase 14 hardening commit: `ba8e7c5dbbde6df7f39aba07f50efde3984c56d4`.
- HTTPS verification documentation commit: `d8f20a86b324efb14bf3d86cf6cd0a322ca859fd`.
- Inventory-location creation commit: `fbf5ff74fc3347f5ec5346c4411e639422d08774`.
- Latest CI: **102 passed, 6 opt-in Sandbox tests skipped**.
- Latest CI fresh migration chain: PASS.
- Latest CI clean-tree check: PASS.
- Previous public check showed HTTPS working while `/health` returned 404, indicating the VPS was serving an older tree at that time. The current source now contains `/health`; deployment must be re-verified rather than treating that old 404 as an application-code defect.

## Definition of Done

Phase 14 is complete only when the latest GitHub `main` is deployed, live Production connection/defaults are verified, Docker restart behavior is verified, and one intentional low-risk listing completes the entire workflow and is confirmed live on eBay Canada.

---

# MASTER MVP ACCEPTANCE TEST

The project is not complete until this passes in one controlled Production workflow.

- [ ] Open current deployed app.
- [ ] Log in.
- [ ] Confirm eBay Settings shows Production and `EBAY_CA`.
- [ ] Confirm connected real seller account.
- [ ] Confirm payment/fulfillment/return defaults.
- [ ] Confirm usable default merchant location.
- [ ] Click New Listing.
- [ ] Upload at least 3 images.
- [ ] Add seller notes.
- [ ] Analyze.
- [ ] Confirm structured product information.
- [ ] Confirm eBay category.
- [ ] Confirm required item specifics.
- [ ] Confirm active comparables.
- [ ] Confirm recommended/final price.
- [ ] Confirm generated title/description/condition.
- [ ] Edit at least one generated field and verify the manual edit persists.
- [ ] Resolve validator errors.
- [ ] Approve listing.
- [ ] Upload images to eBay.
- [ ] Stage Inventory Item.
- [ ] Stage Offer.
- [ ] Review final publish confirmation.
- [ ] Explicitly publish.
- [ ] Receive and persist listing ID.
- [ ] Display Published state.
- [ ] Refresh without creating a duplicate listing.
- [ ] Confirm listing remains recorded locally.
- [ ] Confirm listing is live on eBay Canada.

---

# EXECUTION ORDER FROM CURRENT STATE

Do **not** restart completed implementation phases unless a regression requires it.

```text
NOW
  ↓
Deploy current GitHub main to VPS
  ↓
Verify /health and live application version
  ↓
Verify Production OAuth + EBAY_CA
  ↓
Create/retrieve Production inventory location
  ↓
Refresh and save real seller defaults
  ↓
Verify Docker reboot/restart behavior
  ↓
Run one low-risk full Production listing
  ↓
Record listing ID/URL and Phase 14 evidence
  ↓
Mark Phase 14 + MVP acceptance COMPLETE
```

---

# Multi-account note — future

The MVP remains single-seller. Business logic should continue avoiding assumptions that make future multiple eBay seller profiles impossible. Do not build multi-account UI during the MVP unless it becomes a requirement.

---

# Agent / LLM operating rules

Any coding agent working on this repository must:

1. Read current GitHub `main`, `MASTER_LIST.md`, `PRD.md`, and `setup.md` before changing code.
2. Treat GitHub `main` and this file as the source of truth.
3. Work only on the assigned task/current active phase unless a prerequisite or regression requires otherwise.
4. Never mark a task `[x]` until it is implemented and verified.
5. Add or update tests for important behavior.
6. Run relevant tests before declaring a task complete.
7. Run the full suite when the change can affect shared workflows or before phase certification.
8. Reconcile `MASTER_LIST.md` with actual completed work before finishing.
9. Commit every coherent completed task/phase.
10. Push completed work to `main`; do not leave completion only locally or on the VPS.
11. Verify CI after pushing when CI applies.
12. Keep the app runnable after every completed task.
13. Never hard-code, print, expose, or commit credentials/tokens.
14. Preserve manual seller edits.
15. Never auto-publish AI-generated content.
16. Never change publishing behavior incidentally while implementing an unrelated task.
17. Prefer mocked deterministic tests for eBay behavior; live tests must remain explicit/opt-in unless performing an intentional Production smoke test.
18. Stop and report true external/account blockers instead of inventing eBay behavior.
19. When external verification changes a checklist item, update this file and commit/push that documentation change too.
20. A task is not considered fully closed until its status here matches the actual repository/deployment state.
