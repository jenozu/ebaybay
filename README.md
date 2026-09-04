# eBayBay

Private eBay AI Listing Assistant for eBay Canada (`EBAY_CA`).

## Source of truth

**Start here:** [`MASTER_LIST.md`](MASTER_LIST.md)

`MASTER_LIST.md` is the authoritative phase-by-phase roadmap. A checkbox is only marked complete after the work is actually implemented and verified.

Supporting documents:

- [`PRD.md`](PRD.md) — product/architecture specification
- [`setup.md`](setup.md) — repeatable eBay Sandbox OAuth + VPS setup
- [`UI_STYLE_GUIDE.md`](UI_STYLE_GUIDE.md) — approved neo-brutalist pastel visual system and color palette

## Current status

We intentionally solved the difficult eBay Sandbox/OAuth foundation before building the main listing application.

Verified successfully:

- eBay Developer Sandbox keyset created
- Sandbox seller created
- OAuth RuName configured
- HTTPS callback hosted at `ebaybay.andel-vps.space`
- OAuth scopes `sell.inventory` and `sell.account`
- Authorization Code flow completed
- callback automatically exchanges the code
- access + refresh tokens received
- refresh token saved persistently on the VPS
- refresh-token grant tested
- Sell Inventory API smoke test passed
- MVP visual theme approved and documented

Final smoke test:

```text
GET https://api.sandbox.ebay.com/sell/inventory/v1/getVersion
HTTP 200
{"version":"1.0.0"}
```

The AI listing application itself is **not built yet**. We now return to Phase 0/1 in `MASTER_LIST.md` and build the product incrementally.

## Infrastructure

- Host: Hostinger VPS
- App folder: `/opt/docker/ebaybay`
- Runtime: Docker + Flask + Gunicorn
- Public host: `https://ebaybay.andel-vps.space`
- Persistent token path: `/opt/docker/ebaybay/data/token.json`

## Security

Never commit or display:

- `.env`
- Client Secret / Cert ID
- access tokens
- refresh tokens
- `data/token.json`

Use `.env.example` for non-secret configuration names/placeholders only.
