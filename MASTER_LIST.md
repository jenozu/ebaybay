# eBayBay — Master Build & Production Readiness List

**Status:** ACTIVE SOURCE OF TRUTH  
**Last reconciled:** 2026-09-13  
**Repository:** `jenozu/ebaybay`  
**Branch:** `main`  
**Marketplace:** eBay Canada (`EBAY_CA`)  
**Public host:** `https://ebaybay.andel-vps.space`  
**Deployment:** Hostinger VPS, `/opt/docker/ebaybay`

> GitHub `main` plus this file define the current project state. A coherent task is complete only when it is implemented, tested, documented here, committed, pushed, and CI-verified when CI applies.

## Completion and Git discipline

- `[ ]` = incomplete, blocked, or not yet verified.
- `[x]` = implemented and verified.
- Never mark work complete because code was merely drafted or discussed.
- Never mark a phase complete until its Definition of Done is satisfied.
- Every coherent completed task/phase must end with: relevant tests → `MASTER_LIST.md` reconciliation → Git commit → push to `main` → CI verification when applicable.
- Do not leave completed work only on a VPS, workstation, temporary branch, or uncommitted worktree.
- GitHub `main` is the application-code source of truth. Deploy the VPS from `main`; avoid manual source edits on the VPS.
- Never commit or expose `.env`, Client Secrets, access/refresh tokens, encryption keys, passwords, or `data/token.json`.
- Production publishing always requires human review and explicit publish confirmation.
- Unrelated implementation work must not incidentally change inventory, offer, or publish behavior.

---

# CURRENT REALITY — September 13, 2026

## Current verified application state

- [x] Phases 1–13 are implemented in the main application.
- [x] Private login, CSRF, secure sessions, database persistence, migrations, and `/health` are implemented.
- [x] Draft creation, image upload, seller notes, edit/archive/delete workflow are implemented.
- [x] AI analysis, taxonomy/item specifics, active comps/pricing, and listing writer are implemented.
- [x] Internal validation and explicit human approval are implemented.
- [x] Shared eBay OAuth connection service is implemented.
- [x] Seller policy retrieval/default persistence and inventory-location retrieval are implemented.
- [x] Production-safe inventory-location creation from Settings is implemented.
- [x] eBay Media image-resource workflow is implemented with multipart upload, `201 Created`, `Location` parsing, `getImage`, ID/URL persistence, retries, and local idempotency.
- [x] Media API now uses the current Commerce path `/commerce/media/v1_beta/...`.
- [x] Media API now uses the Media gateway host (`apim.ebay.com` / `apim.sandbox.ebay.com`) rather than the normal REST host.
- [x] Inventory Item staging, unpublished Offer staging, and controlled publishing are implemented.
- [x] Current Media gateway code commit on `main`: `c1d5b42d39810b1a8ac25393bb4d66ab373513f7`.
- [x] CI for that exact Media gateway commit passed: **111 passed, 6 opt-in tests skipped**.
- [x] Fresh-database migration verification passed.
- [x] Repository clean-tree verification passed.

## Current active objective

**Phase 14 — Production Readiness** remains active. The implementation phases are built; remaining work is live Production verification and the first intentional low-risk listing.

## Live verification already completed

- [x] Repeatable VPS deployment workflow (`git pull` → Docker rebuild/restart) has been exercised successfully.
- [x] Public HTTPS host is reachable.
- [x] Public `/health` returned HTTP 200 with `{"status":"ok"}` on 2026-09-13.
- [x] VPS was confirmed running Media-path commit `7be0546bb6d611b56b6e8fba62cb88576aa7f0d6` before the latest gateway-host correction.
- [x] Live image-upload test reached the eBay request path without a Flask crash.
- [x] Live test on `7be0546` returned a deterministic eBay rejection, which exposed that Media was still being sent to the normal REST host.
- [x] Media gateway-host correction was implemented and fully tested in `c1d5b42d39810b1a8ac25393bb4d66ab373513f7`.

## Immediate next actions

- [ ] Deploy current `main` including `c1d5b42d39810b1a8ac25393bb4d66ab373513f7` to the VPS.
- [ ] Re-verify `/health` after that deployment.
- [ ] Retry **Upload Approved Images to eBay** against the real Production account.
- [ ] If Media still fails, capture a safe structured eBay error code/status without logging credentials or raw sensitive response data.
- [ ] Verify the real Production seller connection, policies, inventory location, and saved defaults in Settings.
- [ ] Verify Docker auto-restart after an actual VPS reboot.
- [ ] Run one controlled low-risk Production listing through the complete workflow.
- [ ] Record the first Production listing ID/URL and final evidence here.

---

# PHASE 0 — Project Initialization

**Status: FUNCTIONALLY COMPLETE**

- [x] GitHub repository, Flask app factory, Python/Gunicorn baseline.
- [x] `.gitignore` / `.dockerignore` secrets protection.
- [x] `.env.example`, `README.md`, `setup.md`, `PRD.md`, `MASTER_LIST.md`.
- [x] Dockerfile and Compose configuration.
- [x] persistent database/uploads support.
- [x] `/health` route.
- [x] Docker restart policy configured.
- [x] Repeatable VPS pull/build/restart workflow exercised successfully.
- [ ] Auto-restart after an actual VPS reboot verified.

---

# PHASE 1 — Core Draft Application

**Status: COMPLETE**

- [x] Flask configuration, SQLAlchemy/Alembic, persistent SQLite.
- [x] Listing, ListingImage, ListingAspect, ComparableListing, and eBay connection persistence.
- [x] Private single-user authentication, password hashing, secure session configuration, CSRF, no public registration.
- [x] Dashboard/New Listing, multiple image uploads, seller notes, unique SKU.
- [x] Save/reopen/edit/archive/delete workflows and listing state display.
- [x] Automated draft/auth/upload tests.

**Definition of Done:** local draft workflow works without AI or eBay APIs.

---

# PHASE 2 — AI Product Analysis

**Status: COMPLETE**

- [x] Provider abstraction and structured product-analysis schema.
- [x] Product/brand/model/MPN/GTIN and condition/confidence handling.
- [x] Observations/search terms/detected attributes/uncertainty handling.
- [x] No invention of unseen facts; seller-note precedence.
- [x] Structured-response validation and raw audit persistence.
- [x] Editable populated fields, regeneration, manual-edit preservation.
- [x] Mocked provider/schema/workflow tests.

---

# PHASE 3 — eBay Developer + Sandbox Foundation

**Status: FUNCTIONALLY COMPLETE**

- [x] Sandbox keyset, seller authorization, RuName/callback flow.
- [x] Required seller scopes, authorization-code exchange, access/refresh token flow.
- [x] Authenticated Inventory API call proven.
- [x] Credentials kept outside Git.
- [ ] Optional separate Sandbox buyer account if future transaction testing requires it.

---

# PHASE 4 — Taxonomy + Item Specifics

**Status: COMPLETE**

- [x] `EBAY_CA` taxonomy service, suggestions, manual override, persisted category path.
- [x] Required/recommended aspects and AI attribute mapping.
- [x] Missing-required-aspect validation and deterministic mocked tests.

**Historical certification:** 33 tests passed.

---

# PHASE 5 — Active Comparable Search + Pricing

**Status: COMPLETE**

- [x] Browse API service and prioritized product-search terms.
- [x] Active comparable retrieval, shipping/currency normalization, persistence, similarity scoring, weak-match filtering.
- [x] Range/median/quick-sale/recommended/high pricing and confidence explanation.
- [x] Manual final-price preservation and mocked tests.

**Historical certification:** 47 tests passed.

---

# PHASE 6 — Listing Writer

**Status: COMPLETE**

- [x] Evidence-grounded title, description, and condition generators.
- [x] eBay title-length enforcement and anti-keyword-stuffing/invention guards.
- [x] Generated-copy persistence, regeneration controls, manual-copy preservation.

**Historical certification:** 59 tests passed.  
**Completion commit:** `93726d00a062a2f9d22d7ef67742949aa891a1b2`.

---

# PHASE 7 — Internal Validation + Human Approval

**Status: COMPLETE**

- [x] Validation for images/title/condition/quantity/price/category/SKU/aspects.
- [x] Policy, merchant-location, marketplace, format, OAuth, title-length, and price-precision validation.
- [x] Grouped UI errors, explicit Approve Listing, READY transition rules, Return to Draft.
- [x] Approved-listing edit/AI overwrite protection and state-transition tests.

**Historical certification:** 68 tests passed.  
**Completion commit:** `02ccbf22`.

---

# PHASE 8 — eBay OAuth User Connection

**Status: COMPLETE**

- [x] Settings / Connect eBay page and reusable OAuth service.
- [x] State verification, encrypted refresh-token persistence, token expiry/refresh.
- [x] Connected/disconnected/reconnect/disconnect flows and safe revoked-auth handling.
- [x] Token secrecy and deterministic OAuth tests.

**Historical certification:** 75 passed, 1 opt-in Sandbox test skipped.  
**Completion commit:** `4b2c21ef`.

---

# PHASE 9 — Seller Policies + Inventory Location

**Status: COMPLETE (implementation)**

- [x] Payment, fulfillment, and return policy retrieval.
- [x] Inventory-location retrieval with pagination.
- [x] Settings dropdowns and saved default policy/location IDs.
- [x] `EBAY_CA` locked/validated for MVP and stale-default validation before staging.
- [x] Production-safe `create_inventory_location()` using `POST /sell/inventory/v1/location/{merchantLocationKey}`.
- [x] Merchant key/name/address/city/state-province/postal/country, default `WAREHOUSE`, enabled/disabled support.
- [x] Validation, URL encoding, authentication, CSRF, and no credential exposure.
- [x] Location-only refresh preserves cached policies and makes enabled created location selectable.
- [x] Mocked endpoint/payload/error/cache/security tests.
- [x] No offer/publish behavior changes.
- [x] Inventory-location feature has been included in deployed VPS builds.
- [ ] Real Production inventory-location creation/retrieval positively verified in the live account.

**Inventory-location completion commit:** `fbf5ff74fc3347f5ec5346c4411e639422d08774`.  
**CI at that checkpoint:** 102 passed, 6 skipped.

---

# PHASE 10 — eBay Image Upload

**Status: COMPLETE (implementation); Production verification in Phase 14**

- [x] eBay Media service and approved local image upload.
- [x] Multipart `createImageFromFile` upload using `files={"image": (filename, content, mime_type)}` without manually setting multipart `Content-Type`.
- [x] `201 Created` handling and `Location` response parsing.
- [x] Image ID derivation and `GET /commerce/media/v1_beta/image/{image_id}` lookup.
- [x] eBay/EPS image ID and hosted URL persistence.
- [x] Current Commerce Media path `/commerce/media/v1_beta`.
- [x] Current Media gateway host `apim.ebay.com` / `apim.sandbox.ebay.com`.
- [x] Canonical shared `EBAY_API_BASE` values are translated for Media while custom/mock bases remain supported.
- [x] Image ordering, upload state, bounded transient retries, safe errors, duplicate/idempotency handling.
- [x] If create succeeds but `getImage` fails, persisted remote ID is reused rather than creating a duplicate.
- [x] Approval/READY gating preserved.
- [x] Deterministic multipart/201/Location/getImage/malformed/retry/persistence/host-selection coverage.
- [x] Inventory/offer/publish behavior unchanged.
- [ ] Latest Media gateway fix deployed and positively verified against Production.

**Historical Phase 10 certification:** 83 passed, 3 skipped.  
**Multipart/current-flow commit:** `32915e55543ae8cdb167bc23c38a17d3e7db2671`.  
**Commerce-path commit:** `7be0546bb6d611b56b6e8fba62cb88576aa7f0d6`.  
**Media gateway code commits:** `67fa213694f59038bc7dbcdb07eec56187b1ef4b`, `c1d5b42d39810b1a8ac25393bb4d66ab373513f7`.  
**Latest CI:** 111 passed, 6 skipped; fresh migration PASS; clean-tree PASS.

---

# PHASE 11 — Inventory Item Staging

**Status: COMPLETE**

- [x] Inventory API service and Listing → Inventory Item payload mapping.
- [x] SKU/condition/aspects/product/image/quantity mapping.
- [x] `createOrReplaceInventoryItem`, staging persistence, validation/API error handling, idempotent retry.
- [x] Mocked + opt-in integration coverage.

**Historical certification:** 87 passed, 4 skipped.  
**Completion commit:** `cfcd880af9ce7014cc39b89e20b1c6892f9691df`.

---

# PHASE 12 — Offer Staging

**Status: COMPLETE**

- [x] Offer payload mapping for SKU/category/marketplace/quantity/price/currency.
- [x] Fixed-price format, duration, policy IDs, merchant location.
- [x] Create Offer, offer ID persistence, `EBAY_STAGED`, safe retry/duplicate handling.
- [x] Mocked + opt-in integration coverage.

**Historical certification:** 91 passed, 5 skipped.  
**Completion commit:** `7e4092bc427253bc8b0f39b3cb6469a66f3ebaeb`.

---

# PHASE 13 — Controlled Publish Workflow

**Status: COMPLETE**

- [x] Final review panel and visually distinct Publish action.
- [x] Explicit confirmation requirement.
- [x] `publish_offer(offer_id)`, listing ID/timestamp/URL persistence, `PUBLISHED` state.
- [x] Double-publish protection and safe failed/unknown-outcome handling.
- [x] Success screen, mocked tests, opt-in Sandbox publish coverage.

**Historical certification:** 94 passed, 6 skipped.  
**Completion commit:** `38c16c5dd6bd9bbdbaad0ca1767cdeb4b9a21e9a`.

---

# PHASE 14 — Production Readiness

## Goal

Safely run the current application against the real seller account and intentionally publish one low-risk eBay Canada listing.

**Status: IN PROGRESS**

## Production configuration

Only check external/account-level items when positively verified against the currently deployed Production setup.

- [ ] Production eBay keyset positively verified against the currently deployed app configuration.
- [ ] Production RuName positively verified.
- [ ] Production callback/privacy/declined URLs positively verified.
- [x] Environment switching (`sandbox` / `production`) implemented.
- [ ] Real seller OAuth connection positively verified in the current deployed app.
- [ ] Real payment policies retrieved in current deployed app.
- [ ] Real fulfillment policies retrieved in current deployed app.
- [ ] Real return policies retrieved in current deployed app.
- [ ] Real inventory location created/retrieved in current deployed app.
- [ ] Real seller defaults saved.
- [x] `EBAY_CA` application validation implemented.
- [ ] `EBAY_CA` positively confirmed in the live Production Settings flow.

## App hardening / deployment

- [x] Production login, HTTPS, debug disabled, Gunicorn, structured logging.
- [x] Credential redaction / secrets absent from normal logs.
- [x] CSRF/session protections.
- [x] Database backup tooling and documented/tested restore procedure.
- [x] Upload-cleanup policy.
- [x] `/health` route implemented.
- [x] VPS pull → Docker build/restart deployment workflow verified.
- [x] Live public `/health` HTTP 200 verified on 2026-09-13.
- [ ] Current newest `main` (`c1d5b42...` plus this reconciliation commit) deployed after Media gateway correction.
- [ ] Docker auto-restart after an actual VPS reboot verified.

## Production Media verification

- [x] Multipart Media upload implementation corrected.
- [x] Commerce Media `/commerce/media/v1_beta` path corrected.
- [x] Live test on path-corrected build reached eBay and returned a non-transient rejection rather than an app crash/time-out.
- [x] Media-specific `apim` gateway-host correction implemented and tested.
- [ ] Deploy gateway correction to VPS.
- [ ] Retry Production image upload and persist a real eBay image ID + EPS URL successfully.

## First real smoke test

- [ ] Choose one low-risk item.
- [ ] Create/open draft.
- [ ] Upload images and notes.
- [ ] Analyze.
- [ ] Confirm category and required aspects.
- [ ] Review active comparables and final price.
- [ ] Generate/review title, description, and condition text.
- [ ] Resolve validation issues.
- [ ] Approve listing.
- [ ] Upload images to eBay.
- [ ] Stage Inventory Item.
- [ ] Stage Offer.
- [ ] Review final publish panel.
- [ ] Explicitly confirm publish.
- [ ] Publish successfully.
- [ ] Persist listing ID/URL.
- [ ] Verify listing on eBay Canada.
- [ ] Record smoke-test evidence here.

## Latest readiness evidence

- Phase 14 hardening commit: `ba8e7c5dbbde6df7f39aba07f50efde3984c56d4`.
- HTTPS verification documentation commit: `d8f20a86b324efb14bf3d86cf6cd0a322ca859fd`.
- Inventory-location creation commit: `fbf5ff74fc3347f5ec5346c4411e639422d08774`.
- Media multipart/current response-flow commit: `32915e55543ae8cdb167bc23c38a17d3e7db2671`.
- Media Commerce-path commit: `7be0546bb6d611b56b6e8fba62cb88576aa7f0d6`.
- Media gateway latest code commit: `c1d5b42d39810b1a8ac25393bb4d66ab373513f7`.
- Latest code CI: **111 passed, 6 opt-in tests skipped**.
- Fresh migration chain: PASS.
- Clean-tree verification: PASS.
- VPS deployment through `7be0546` and live `/health` HTTP 200 were positively verified on 2026-09-13.
- Live image-upload test on `7be0546` returned “eBay rejected the image upload,” leading to the `apim` gateway-host correction now awaiting deployment.

## Definition of Done

Phase 14 is complete only when the latest GitHub `main` is deployed, real Production connection/defaults are verified, Docker reboot behavior is verified, and one intentional low-risk listing completes the entire workflow and is confirmed live on eBay Canada.

---

# MASTER MVP ACCEPTANCE TEST

- [ ] Open current deployed app and log in.
- [ ] Confirm Settings shows Production and `EBAY_CA`.
- [ ] Confirm connected real seller account.
- [ ] Confirm payment/fulfillment/return defaults and usable merchant location.
- [ ] Create a New Listing and upload at least 3 images.
- [ ] Add seller notes and analyze.
- [ ] Confirm structured product information, category, and required item specifics.
- [ ] Confirm active comparables and final price.
- [ ] Confirm generated title/description/condition.
- [ ] Edit at least one generated field and verify the manual edit persists.
- [ ] Resolve validator errors and approve.
- [ ] Upload images to eBay and persist hosted image resources.
- [ ] Stage Inventory Item.
- [ ] Stage Offer.
- [ ] Review final publish confirmation and explicitly publish.
- [ ] Receive/persist listing ID and display Published state.
- [ ] Refresh without creating a duplicate listing.
- [ ] Confirm listing remains recorded locally and is live on eBay Canada.

---

# EXECUTION ORDER FROM CURRENT STATE

Do **not** restart completed implementation phases unless a regression requires it.

```text
NOW
  ↓
Deploy current GitHub main to VPS
  ↓
Verify /health
  ↓
Retry Production Media image upload
  ↓
If successful, verify Production OAuth + EBAY_CA + seller policies/location/defaults
  ↓
Verify Docker reboot/restart behavior
  ↓
Run one low-risk full Production listing
  ↓
Record listing ID/URL and final Phase 14 evidence
  ↓
Mark Phase 14 + MVP acceptance COMPLETE
```

---

# Multi-account note — future

The MVP remains single-seller. Business logic should avoid assumptions that make future multiple eBay seller profiles impossible. Do not build multi-account UI during the MVP unless it becomes a requirement.

---

# Agent / LLM operating rules

Any coding agent working on this repository must:

1. Read current GitHub `main`, `MASTER_LIST.md`, `PRD.md`, and `setup.md` before changing code.
2. Treat GitHub `main` and this file as the source of truth.
3. Work only on the assigned task/current active phase unless a prerequisite or regression requires otherwise.
4. Never mark a task `[x]` until it is implemented and verified.
5. Add/update tests for important behavior.
6. Run relevant tests before declaring a task complete.
7. Run the full suite when shared workflows can be affected or before phase certification.
8. Reconcile `MASTER_LIST.md` before finishing.
9. Commit every coherent completed task/phase.
10. Push completed work to `main`; do not leave completion only locally or on the VPS.
11. Verify CI after pushing when CI applies.
12. Keep the app runnable after every completed task.
13. Never hard-code, print, expose, or commit credentials/tokens.
14. Preserve manual seller edits.
15. Never auto-publish AI-generated content.
16. Never change publishing behavior incidentally while implementing unrelated work.
17. Prefer deterministic mocked eBay tests; live tests remain explicit/opt-in except intentional Production smoke tests.
18. Stop and report true external/account blockers instead of inventing eBay behavior.
19. When external verification changes a checklist item, update this file and commit/push that documentation change.
20. A task is not fully closed until this file matches the actual repository/deployment state.
