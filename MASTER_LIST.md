# eBayBay — Master Build & Production Readiness List

**Status:** ACTIVE SOURCE OF TRUTH  
**Last reconciled:** 2026-09-14
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

# CURRENT REALITY — September 14, 2026

## Current verified application state

- [x] Phases 1–13 are implemented in the main application.
- [x] Private login, CSRF, secure sessions, database persistence, migrations, and `/health` are implemented.
- [x] Draft creation, image upload, seller notes, edit/archive/delete workflow are implemented.
- [x] Existing-image edit/save handling is hardened: persisted `ListingImage` rows no longer populate the upload-only form field or crash saves with `AttributeError: 'ListingImage' object has no attribute 'stream'`.
- [x] AI analysis, taxonomy/item specifics, active comps/pricing, and listing writer are implemented.
- [x] Internal validation and explicit human approval are implemented.
- [x] Shared eBay OAuth connection service is implemented.
- [x] Seller policy retrieval/default persistence and inventory-location retrieval are implemented.
- [x] Production-safe inventory-location creation from Settings is implemented.
- [x] eBay Media image-resource workflow is implemented with multipart upload, `201 Created`, `Location` parsing, `getImage`, ID/URL persistence, retries, and local idempotency.
- [x] Media API uses the current Commerce path `/commerce/media/v1_beta/...` and Media gateway host (`apim.ebay.com` / `apim.sandbox.ebay.com`).
- [x] Production Media upload is positively verified: one approved image was accepted by eBay and persisted as an eBay-hosted image resource on 2026-09-13.
- [x] Inventory Item staging, unpublished Offer staging, and controlled publishing are implemented.
- [x] Inventory staging validates/classifies UPC/EAN/ISBN identifiers instead of blindly sending every GTIN as EAN.
- [x] Inventory staging sends Canadian locale headers for `EBAY_CA` and URL-encodes SKU path values.
- [x] Inventory staging records only safe eBay rejection diagnostics: HTTP status plus whitelisted error ID/domain/category/message; tokens, headers, raw bodies, arbitrary fields, and parameter values are excluded.
- [x] Inventory staging now retries transient transport failures and HTTP `429/500/502/503/504` responses up to three attempts with bounded delay and `Retry-After` support.
- [x] Latest Inventory retry hardening CI passed: **118 passed, 6 opt-in tests skipped**.
- [x] Production OAuth, Media upload, Inventory Item staging, unpublished Offer staging, and final publishing have all been proven working.
- [x] The completed Production listing reached `PUBLISHED` locally and the app displayed `Listing published successfully`.
- [x] The lean seller dashboard is implemented locally using real listing and cached setup state; deployment was intentionally excluded from this task.
- [x] Dashboard/full regression result: **125 passed, 6 opt-in tests skipped**.
- [x] Fresh-database migration verification passed.
- [ ] Dashboard completion commit pushed and GitHub CI verified.

## Current active objective

**Phase 15 — Lean Seller Dashboard** is the active code objective. The dashboard implementation and local verification are complete; the remaining task is to commit/push the tested tree and verify GitHub CI. VPS deployment is intentionally deferred until explicitly requested.

## Live verification already completed

- [x] Repeatable VPS deployment workflow (`git pull` → Docker rebuild/restart) has been exercised successfully.
- [x] Public HTTPS host is reachable.
- [x] Public `/health` returned HTTP 200 with `{"status":"ok"}` on 2026-09-13.
- [x] Media Commerce path and `apim` gateway corrections were deployed to the VPS.
- [x] Production image upload succeeded: UI reported `1 uploaded, 0 already current` and the eBay-hosted image resource was persisted.
- [x] The next live step reached `createOrReplaceInventoryItem` without a Flask crash.
- [x] Initial Inventory staging was rejected while the test draft contained the placeholder value `GTIN = Test GTIN`.
- [x] Code inspection confirmed the old payload incorrectly mapped any non-empty GTIN to `product.ean`.
- [x] Inventory identifier/locale hardening was implemented, tested, deployed, and the test draft was successfully edited to remove fake Product/Brand/Model/MPN/GTIN values.
- [x] A separate live edit/save attempt exposed a 500 caused by the edit form treating persisted `ListingImage` rows as new upload objects.
- [x] The edit/save root cause was fixed, regression-tested, deployed, and subsequent edit/validation requests completed normally.
- [x] Safe Inventory diagnostics were deployed and positively verified in Production.
- [x] Cleaned Inventory staging request returned `HTTP 500`, eBay error `25001`, domain `API_INVENTORY`, category `Request`, message `A system error has occurred. Core Inventory Service internal error`.
- [x] eBay guidance classifies HTTP 500/server faults as retryable and recommends bounded retries; current eBay API status also shows an unresolved selling/listing system-error incident.
- [x] A subsequent Production Inventory Item stage succeeded.
- [x] A Production unpublished Offer stage succeeded.
- [x] Final Production publishing succeeded and the listing persisted locally as `PUBLISHED`.

## Immediate next actions

- [ ] Push the tested Phase 15 dashboard implementation and verify GitHub CI.
- [ ] Deploy the dashboard to the VPS only after an explicit deployment request.
- [ ] Verify Docker auto-restart after an actual VPS reboot.

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
- [x] Existing saved images remain separate from the upload-only edit field; editing without a new upload preserves current images and no longer crashes.
- [x] Automated draft/auth/upload/edit regression tests.

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
- [x] GTIN validation now blocks invalid placeholder/malformed UPC/EAN/ISBN values before approval.
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

**Status: COMPLETE — Production verified 2026-09-13**

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
- [x] Media gateway fix deployed and positively verified against Production: one approved image uploaded successfully and persisted as an eBay-hosted resource.

**Historical Phase 10 certification:** 83 passed, 3 skipped.  
**Multipart/current-flow commit:** `32915e55543ae8cdb167bc23c38a17d3e7db2671`.  
**Commerce-path commit:** `7be0546bb6d611b56b6e8fba62cb88576aa7f0d6`.  
**Media gateway code commits:** `67fa213694f59038bc7dbcdb07eec56187b1ef4b`, `c1d5b42d39810b1a8ac25393bb4d66ab373513f7`.  
**Production verification:** PASS on 2026-09-13.

---

# PHASE 11 — Inventory Item Staging

**Status: COMPLETE (implementation); Production blocked by retryable eBay HTTP 500/25001**

- [x] Inventory API service and Listing → Inventory Item payload mapping.
- [x] SKU/condition/aspects/product/image/quantity mapping.
- [x] `createOrReplaceInventoryItem`, staging persistence, validation/API error handling, idempotent retry.
- [x] Product identifier handling classifies valid UPC-12, EAN-8/EAN-13, ISBN-10/ISBN-13 into the correct Inventory API field.
- [x] Invalid placeholder/malformed GTIN values are blocked locally instead of being sent as `product.ean`.
- [x] `EBAY_CA` Inventory requests send `Content-Language: en-CA` and `Accept-Language: en-CA`.
- [x] Inventory Item SKU is URL-encoded in the endpoint path.
- [x] Safe eBay rejection diagnostics expose only status/error ID/domain/category/message and exclude credentials, raw response bodies, arbitrary fields, and parameters.
- [x] Transient transport failures and HTTP `429/500/502/503/504` responses are retried up to three attempts with bounded delay and simple `Retry-After` support.
- [x] Mocked + opt-in integration coverage.
- [x] Inventory hardening full suite: **114 passed, 6 skipped**; migration PASS; clean-tree PASS.
- [x] Edit-save regression suite on top of Inventory hardening: **115 passed, 6 skipped**; migration PASS; clean-tree PASS.
- [x] Safe diagnostics suite: **116 passed, 6 skipped**.
- [x] Retry hardening suite: **118 passed, 6 skipped**; migration PASS; clean-tree PASS.
- [x] Live cleaned Production request positively identified eBay-side `HTTP 500 / 25001 / Core Inventory Service internal error`.
- [ ] Deploy retry-hardening `main` and re-test `Stage eBay Inventory Item`.

**Historical certification:** 87 passed, 4 skipped.  
**Original completion commit:** `cfcd880af9ce7014cc39b89e20b1c6892f9691df`.  
**Safe diagnostics commit:** `8d3c72d0b86552e3877387cc458b94e218673773`.  
**Transient retry code/test commits:** `c0658c4ea9738f5c7a37e7d35eafe486505750d9`, `bb52409b9a596fd6b90d6236beb0f70acd90c882`.

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

**Status: FUNCTIONALLY COMPLETE — actual VPS reboot verification remains**

## Production configuration

Only check external/account-level items when positively verified against the currently deployed Production setup.

- [x] Production eBay keyset positively verified through the working deployed OAuth/API flow.
- [x] Production RuName positively verified through the working deployed OAuth callback.
- [x] Production callback/privacy/declined configuration proven sufficient for the successful OAuth flow.
- [x] Environment switching (`sandbox` / `production`) implemented.
- [x] Real seller OAuth connection positively verified in the current deployed app.
- [x] Real payment policy/default proven through successful Offer staging.
- [x] Real fulfillment policy/default proven through successful Offer staging.
- [x] Real return policy/default proven through successful Offer staging.
- [x] Real inventory location/default proven through successful Inventory and Offer staging.
- [x] Real seller defaults saved and used successfully.
- [x] `EBAY_CA` application validation implemented.
- [x] `EBAY_CA` positively confirmed by the completed Production listing workflow.

## App hardening / deployment

- [x] Production login, HTTPS, debug disabled, Gunicorn, structured logging.
- [x] Credential redaction / secrets absent from normal logs.
- [x] CSRF/session protections.
- [x] Database backup tooling and documented/tested restore procedure.
- [x] Upload-cleanup policy.
- [x] `/health` route implemented.
- [x] VPS pull → Docker build/restart deployment workflow verified.
- [x] Live public `/health` HTTP 200 verified on 2026-09-13.
- [x] Media gateway correction deployed successfully.
- [x] Existing-image edit/save crash fix deployed and live edit/save no longer crashes.
- [x] Safe Inventory rejection diagnostics deployed and verified against Production.
- [x] Inventory retry hardening was followed by successful Production Inventory staging.
- [ ] Docker auto-restart after an actual VPS reboot verified.

## Production Media verification

- [x] Multipart Media upload implementation corrected.
- [x] Commerce Media `/commerce/media/v1_beta` path corrected.
- [x] Media-specific `apim` gateway-host correction implemented and tested.
- [x] Gateway correction deployed to VPS.
- [x] Production image upload succeeded and persisted a real eBay-hosted image resource on 2026-09-13.

## Production Inventory verification

- [x] Live Production `Stage eBay Inventory Item` request reached eBay on 2026-09-13.
- [x] Initial request was rejected while the test draft contained `GTIN = Test GTIN`.
- [x] Root app defect identified: all non-empty GTIN values were being blindly sent as EAN.
- [x] GTIN classification/checksum validation, Canadian locale headers, and SKU path encoding implemented and deployed.
- [x] Full Inventory-hardening CI passed: **114 passed, 6 skipped**.
- [x] Edit/save 500 was traced to persisted `ListingImage` objects entering the upload field; fix deployed with live edit/save success.
- [x] Safe error diagnostics were deployed; cleaned Production request returned `HTTP 500`, eBay error `25001`, `Core Inventory Service internal error`.
- [x] Deterministic retry hardening added for network faults and HTTP `429/500/502/503/504`; CI passed **118 passed, 6 skipped**.
- [x] Re-test Inventory staging successfully.
- [ ] If 25001 persists after all three attempts, treat it as an eBay-side operational blocker rather than mutating valid listing data without evidence.

## First real smoke test

- [x] Choose one low-risk item and create/open its draft.
- [x] Upload images and prepare/review listing data.
- [x] Resolve validation issues and approve the listing.
- [x] Upload images to eBay.
- [x] Stage Inventory Item.
- [x] Stage Offer.
- [x] Review final publish panel and explicitly confirm publishing.
- [x] Publish successfully.
- [x] Persist the listing as `PUBLISHED` and display the successful result.

## Latest readiness evidence

- Phase 14 hardening commit: `ba8e7c5dbbde6df7f39aba07f50efde3984c56d4`.
- HTTPS verification documentation commit: `d8f20a86b324efb14bf3d86cf6cd0a322ca859fd`.
- Inventory-location creation commit: `fbf5ff74fc3347f5ec5346c4411e639422d08774`.
- Media multipart/current response-flow commit: `32915e55543ae8cdb167bc23c38a17d3e7db2671`.
- Media Commerce-path commit: `7be0546bb6d611b56b6e8fba62cb88576aa7f0d6`.
- Media gateway code commit: `c1d5b42d39810b1a8ac25393bb4d66ab373513f7`.
- Production Media verification: PASS on 2026-09-13 (`1 uploaded, 0 already current`).
- Inventory hardening CI: **114 passed, 6 opt-in tests skipped**.
- Edit-save crash fix merge commit: `11d8b64b6fb51e159122e718d23dccfd1c71c807`.
- Edit-save regression CI: **115 passed, 6 opt-in tests skipped**.
- Safe Inventory diagnostics commit: `8d3c72d0b86552e3877387cc458b94e218673773`; Production diagnostics confirmed `HTTP 500 / 25001`.
- Inventory retry code/test commits: `c0658c4ea9738f5c7a37e7d35eafe486505750d9`, `bb52409b9a596fd6b90d6236beb0f70acd90c882`.
- Inventory retry CI: **118 passed, 6 opt-in tests skipped**.
- Production Inventory, Offer, and final Publish verification: PASS; app displayed `Listing published successfully` and persisted `PUBLISHED`.
- Fresh migration chain: PASS.
- Clean-tree verification: PASS.

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
- [x] Production Media upload capability positively verified with an approved image.
- [ ] Upload all smoke-test images to eBay and persist hosted image resources.
- [x] Stage Inventory Item.
- [x] Stage Offer.
- [x] Review final publish confirmation and explicitly publish.
- [x] Receive/persist listing ID and display Published state.
- [ ] Refresh without creating a duplicate listing.
- [ ] Confirm listing remains recorded locally and is live on eBay Canada.

---

# PHASE 15 — Lean Seller Dashboard

## Goal

Turn `/dashboard` into the primary, practical command center for finding and continuing listing work without adding analytics or duplicating the existing listing detail workflow.

**Status: IMPLEMENTED AND LOCALLY VERIFIED — push/CI pending**

- [x] Audit existing dashboard, routes, models, templates, seller settings, and command-zone prototype.
- [x] Record the minimal page ownership and workflow in `docs/DASHBOARD_PLAN.md`.
- [x] Render real Drafts, Needs Attention, Ready, and Published counts.
- [x] Add server-rendered All/Drafts/Needs Attention/Ready/Published filtering.
- [x] Add responsive listing queue cards with thumbnail, title fallback, SKU, state, price, updated time, and Open/Continue action.
- [x] Show View on eBay only for published listings with a saved URL.
- [x] Show compact cached/local eBay connection, marketplace, and seller-default health.
- [x] Add deterministic dashboard coverage; full result: **125 passed, 6 opt-in tests skipped**.
- [x] Verify fresh migrations from an empty database through `0011_phase13_publish`.
- [ ] Push the tested implementation and verify GitHub CI.

**Architecture decision:** Keep top-level navigation to Dashboard, New Listing, and Settings. Keep listing detail/edit as workflow destinations. Do not add separate listing/status pages; dashboard filters own those views.

---

# EXECUTION ORDER FROM CURRENT STATE

Do **not** restart completed implementation phases unless a regression requires it.

```text
NOW
  ↓
Push the tested lean dashboard implementation
  ↓
Verify GitHub CI and reconcile Phase 15 as complete
  ↓
Await an explicit request before deploying the dashboard to the VPS
  ↓
Separately verify Docker restart behavior after an actual VPS reboot
```

---

# Multi-account note — future

The MVP remains single-seller. Business logic should avoid assumptions that make future multiple eBay seller profiles impossible. Do not build multi-account UI during the MVP unless it becomes a requirement.
