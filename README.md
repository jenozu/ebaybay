# eBayBay

Automation project for eBay listing workflows.

## Current status

**eBay Sandbox OAuth is working end-to-end.**

Verified successfully:

- eBay Developer Sandbox keyset created
- Sandbox seller created
- OAuth RuName configured
- HTTPS callback hosted at `ebaybay.andel-vps.space`
- OAuth scopes limited to `sell.inventory` and `sell.account`
- Authorization Code flow completed
- Access token received
- Refresh token received and saved on the VPS
- Refresh flow tested
- Sell Inventory API smoke test passed

Final smoke test:

```text
GET https://api.sandbox.ebay.com/sell/inventory/v1/getVersion
HTTP 200
{"version":"1.0.0"}
```

## Infrastructure

- Host: Hostinger VPS
- App folder: `/opt/docker/ebaybay`
- Runtime: Docker + Flask + Gunicorn
- Reverse proxy / TLS: Hostinger Traefik + Let's Encrypt
- Public callback host: `https://ebaybay.andel-vps.space`
- Persistent token path on host: `/opt/docker/ebaybay/data/token.json`

## Security

Never commit any of the following:

- `.env`
- Client Secret / Cert ID
- Access tokens
- Refresh tokens
- `data/token.json`

See [`setup.md`](setup.md) for the complete repeatable setup procedure, including how to repeat the OAuth setup for additional eBay accounts.