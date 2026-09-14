# Lean Seller Dashboard Plan

## Navigation and page ownership

Keep the primary navigation intentionally small:

- **Dashboard** (`/dashboard`) — the listing index and seller work queue.
- **New Listing** (`/listings/new`) — create a draft and upload initial photos.
- **Settings** (`/settings/ebay`) — eBay OAuth, marketplace/environment, seller policies, and inventory location.

Keep the existing listing detail (`/listings/<id>`) and edit (`/listings/<id>/edit`) routes as workflow destinations, not top-level navigation. Existing authenticated POST routes continue to own AI, taxonomy, pricing, validation, approval, Media, Inventory, Offer, publish, archive, restore, and delete actions.

No separate All Listings, Drafts, Ready, or Published pages are needed initially. The dashboard provides `All`, `Drafts`, `Needs Attention`, `Ready`, and `Published` filters. This avoids duplicate controllers and templates while the listing volume is small.

## Dashboard contents

`/dashboard` should render only local database state and contain:

1. A compact heading with New Listing and Settings actions.
2. Four real summary counts: Drafts, Needs Attention, Ready, and Published.
3. A compact local eBay setup summary: connection, configured marketplace, and whether all seller defaults are selected.
4. The filterable listing work queue, ordered by most recently updated.
5. For each listing: first local thumbnail when present, title/product fallback, SKU, status, price, updated time, and an Open/Continue action.
6. A View on eBay link only for published records with a saved `ebay_listing_url`.

Archived listings remain visible under `All` so they can still be opened and restored, but they do not receive a dedicated top-level filter.

## Dashboard state rules

- **Drafts:** `DRAFT` listings.
- **Ready:** approved or staged listings (`READY`, legacy `STAGED`, or `EBAY_STAGED`).
- **Published:** `PUBLISHED` listings.
- **Needs Attention:** listings with a failed/unknown eBay pipeline state, a failed image upload, or a draft missing locally detectable core publishing requirements (photo, title, condition, positive price, category, or required item specific).

The Needs Attention rule intentionally uses persisted local fields. It must not make an eBay API request or refresh OAuth/default caches during dashboard rendering. Counts may overlap: for example, an incomplete draft is both a Draft and Needs Attention.

## Listing click and normal workflow

Opening a queue item goes to the existing listing detail screen, which remains the single management surface for that item. The normal workflow is:

1. New Listing: add photos and known item details.
2. Detail: run preparation tools, review/edit the result, resolve requirements, and approve.
3. Publish: use the existing protected production pipeline and explicit final confirmation.
4. Dashboard: see the published state and open the saved eBay URL.

Media upload, Inventory Item staging, Offer staging, and final publishing remain unchanged in this dashboard task. A later task may orchestrate the already-working internal stages behind one seller-facing Publish action.

## Implementation constraints

- Reuse the existing models and status fields; no migration is required.
- Keep authentication and CSRF behavior unchanged.
- Keep filtering server-rendered with a validated query parameter.
- Keep eBay connection/default health local and cached.
- Add no frontend framework, dependencies, analytics, sales data, or live listing-management API calls.
