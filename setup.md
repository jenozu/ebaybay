# eBayBay Setup Guide

This guide documents the working setup used to connect an eBay Sandbox seller account to the `ebaybay` app through OAuth. It is written so the same process can be repeated later for additional eBay accounts.

> Never commit real Client Secrets, access tokens, refresh tokens, or `.env` files to GitHub.

---

# 1. What this setup proves

When complete, each eBay account should be able to complete this flow:

```text
eBay Developer App
        ↓
Sandbox Client ID + Client Secret
        ↓
RuName
        ↓
Seller OAuth consent
        ↓
HTTPS callback on VPS
        ↓
Authorization code
        ↓
Access token + Refresh token
        ↓
Refresh token saved on VPS
        ↓
Sell Inventory API returns HTTP 200
```

The working smoke test is:

```text
GET https://api.sandbox.ebay.com/sell/inventory/v1/getVersion
```

Expected result:

```text
HTTP 200
{"version":"1.0.0"}
```

---

# 2. eBay credentials you need

For each eBay Developer application/account combination, record:

```text
EBAY_CLIENT_ID
EBAY_CLIENT_SECRET
EBAY_RUNAME
```

Terminology:

```text
App ID   = Client ID
Cert ID  = Client Secret
RuName   = eBay Redirect URL name
```

The Dev ID can also be recorded, but it is not used in the REST OAuth token exchange.

For this project, the marketplace target is:

```text
EBAY_MARKETPLACE_ID=EBAY_CA
```

---

# 3. Create the eBay Sandbox keyset

1. Sign in to the eBay Developers Program.
2. Open **Application Keys**.
3. Create or select an application.
4. Under **Sandbox**, create a keyset.
5. Record:
   - App ID / Client ID
   - Cert ID / Client Secret
   - Dev ID
6. Keep the Cert ID private.

Do not mix Production and Sandbox credentials.

---

# 4. Create a Sandbox seller

From the eBay Developer portal:

1. Open the Sandbox user registration tool.
2. Create a test seller.
3. Use **Canada** as the registration site for the `EBAY_CA` workflow.
4. Save the generated `TESTUSER_...` username and password securely.

The feedback score and registration date can remain at the default test values.

---

# 5. Configure OAuth scopes

Open:

```text
Application Keys → Sandbox → User Tokens
```

Select **OAuth (new security)**.

Use only these scopes for the current MVP:

```text
https://api.ebay.com/oauth/api_scope/sell.inventory
https://api.ebay.com/oauth/api_scope/sell.account
```

Do not select all available scopes.

---

# 6. Create/configure the RuName

In the lower section titled **Get a Token from eBay via Your Application**, create or edit an eBay Redirect URL.

Use OAuth rather than Auth'n'Auth.

Example configuration for this project:

```text
Display Title:
eBayBay

Privacy Policy URL:
https://ebaybay.andel-vps.space/privacy

Auth accepted URL:
https://ebaybay.andel-vps.space/oauth/callback

Auth declined URL:
https://ebaybay.andel-vps.space/oauth/declined
```

Save the generated RuName exactly as eBay displays it.

Important eBay OAuth behavior:

```text
redirect_uri = RuName
```

The OAuth request uses the RuName, not the literal callback URL. eBay maps the RuName to the configured Accepted URL.

---

# 7. Create the DNS record

For the working deployment, the subdomain is:

```text
ebaybay.andel-vps.space
```

In Hostinger DNS, create:

```text
Type: A
Name: ebaybay
Points to: <VPS PUBLIC IPV4>
TTL: default
```

Verify from the VPS:

```bash
nslookup ebaybay.andel-vps.space
```

The returned IP must match the VPS public IPv4 address.

---

# 8. Create the VPS project folder

On the Hostinger VPS:

```bash
mkdir -p /opt/docker/ebaybay
cd /opt/docker/ebaybay
```

---

# 9. Create the Flask OAuth service

Create `requirements.txt`:

```text
Flask==3.1.2
gunicorn==23.0.0
requests==2.32.5
```

Create `app.py`:

```python
from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "eBay OAuth callback service is running."

@app.route("/privacy")
def privacy():
    return """
    <h1>Privacy Policy</h1>
    <p>This is a private development application used to authenticate with eBay
    and perform seller-authorized API actions.</p>
    """

@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")

    if not code:
        return "OAuth callback received, but no authorization code was provided.", 400

    try:
        response = requests.post(
            "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
            auth=(
                os.environ["EBAY_CLIENT_ID"],
                os.environ["EBAY_CLIENT_SECRET"],
            ),
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": os.environ["EBAY_RUNAME"],
            },
            timeout=30,
        )

        data = response.json()

    except Exception as exc:
        return f"""
        <h1>eBay OAuth Failed</h1>
        <p>Token request failed: {type(exc).__name__}</p>
        """, 500

    if response.ok and data.get("access_token") and data.get("refresh_token"):
        os.makedirs("/app/data", exist_ok=True)

        token_path = "/app/data/token.json"

        with open(token_path, "w") as f:
            json.dump(data, f)

        os.chmod(token_path, 0o600)

        return """
        <h1>eBay OAuth Success</h1>
        <p>Access token received: YES</p>
        <p>Refresh token received: YES</p>
        <p>The tokens were saved securely on the VPS.</p>
        """

    return f"""
    <h1>eBay OAuth Failed</h1>
    <p>Error: {data.get('error', 'unknown')}</p>
    <p>Description: {data.get('error_description', 'No description provided')}</p>
    """, 400

@app.route("/oauth/declined")
def oauth_declined():
    return """
    <h1>eBay authorization declined</h1>
    <p>The seller did not grant access.</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

---

# 10. Create the Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

---

# 11. Create `.env`

Create a local VPS-only `.env` file:

```dotenv
EBAY_CLIENT_ID=YOUR_SANDBOX_APP_ID
EBAY_CLIENT_SECRET=YOUR_SANDBOX_CERT_ID
EBAY_RUNAME=YOUR_SANDBOX_RUNAME
```

Lock it down:

```bash
chmod 600 .env
```

Never commit this file.

Verify that the variable names exist without printing their values:

```bash
grep -E '^(EBAY_CLIENT_ID|EBAY_CLIENT_SECRET|EBAY_RUNAME)=' .env | sed 's/=.*/=SET/'
```

Expected:

```text
EBAY_CLIENT_ID=SET
EBAY_CLIENT_SECRET=SET
EBAY_RUNAME=SET
```

---

# 12. Create persistent token storage

```bash
mkdir -p data
chmod 700 data
```

The host token file will eventually be:

```text
/opt/docker/ebaybay/data/token.json
```

Never commit it.

---

# 13. Create `docker-compose.yml`

Use:

```yaml
services:
  ebaybay:
    build: .
    container_name: ebaybay
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "127.0.0.1:8012:8000"
    volumes:
      - ./data:/app/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ebaybay.rule=Host(`ebaybay.andel-vps.space`)"
      - "traefik.http.routers.ebaybay.entrypoints=websecure"
      - "traefik.http.routers.ebaybay.tls.certresolver=letsencrypt"
      - "traefik.http.services.ebaybay.loadbalancer.server.port=8000"
```

The VPS already runs Hostinger's Traefik on ports 80/443, so do not install a competing Nginx reverse proxy on the host.

---

# 14. Build and start the service

```bash
cd /opt/docker/ebaybay
docker compose up -d --build
```

Verify:

```bash
docker compose ps
```

Test locally:

```bash
curl http://127.0.0.1:8012/
```

Expected:

```text
eBay OAuth callback service is running.
```

---

# 15. Verify HTTPS routes

Test:

```bash
curl https://ebaybay.andel-vps.space/
curl https://ebaybay.andel-vps.space/privacy
curl https://ebaybay.andel-vps.space/oauth/declined
curl -i https://ebaybay.andel-vps.space/oauth/callback
```

The callback route should return HTTP 400 when called without an authorization code. That is expected.

---

# 16. Verify Docker received the OAuth variables

```bash
docker exec -i ebaybay python - <<'PY'
import os
for k in ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET", "EBAY_RUNAME"]:
    print(f"{k}: {'SET' if os.getenv(k) else 'MISSING'}")
PY
```

Expected:

```text
EBAY_CLIENT_ID: SET
EBAY_CLIENT_SECRET: SET
EBAY_RUNAME: SET
```

Verify persistent storage:

```bash
docker exec ebaybay ls -ld /app/data
```

---

# 17. Generate the OAuth authorization URL

Generate a URL with only the required scopes:

```bash
docker exec -i ebaybay python - <<'PY'
import os, urllib.parse

params = {
    "client_id": os.environ["EBAY_CLIENT_ID"],
    "redirect_uri": os.environ["EBAY_RUNAME"],
    "response_type": "code",
    "prompt": "login",
    "scope": " ".join([
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.account",
    ]),
}

print(
    "https://auth.sandbox.ebay.com/oauth2/authorize?"
    + urllib.parse.urlencode(params)
)
PY
```

Copy the generated URL into an Incognito/InPrivate browser window.

Sign in using the correct Sandbox `TESTUSER_...` account.

Approve access.

The browser should return to:

```text
https://ebaybay.andel-vps.space/oauth/callback
```

The app should automatically exchange the code.

Successful page:

```text
eBay OAuth Success
Access token received: YES
Refresh token received: YES
The tokens were saved securely on the VPS.
```

---

# 18. Verify token storage safely

Do not print the tokens.

Check that the file exists:

```bash
ls -l data/token.json
```

Then:

```bash
python3 - <<'PY'
import json

d = json.load(open("data/token.json"))
print("Access token:", "YES" if d.get("access_token") else "NO")
print("Refresh token:", "YES" if d.get("refresh_token") else "NO")
print("Access expires in:", d.get("expires_in"))
print("Error:", d.get("error"))
PY
```

Expected:

```text
Access token: YES
Refresh token: YES
Access expires in: 7200
Error: None
```

---

# 19. Test the Inventory API

Run:

```bash
python3 - <<'PY'
import json
import requests

d = json.load(open("data/token.json"))

r = requests.get(
    "https://api.sandbox.ebay.com/sell/inventory/v1/getVersion",
    headers={
        "Authorization": f"Bearer {d['access_token']}"
    },
    timeout=30,
)

print("HTTP status:", r.status_code)
print("Response:", r.text)
PY
```

Expected successful result:

```text
HTTP status: 200
Response: {"version":"1.0.0"}
```

Once this passes, the Sandbox OAuth setup is proven end-to-end.

---

# 20. Test the refresh-token flow

The access token is short-lived. The refresh token is what allows the app to obtain new access tokens without another manual login.

Run:

```bash
python3 - <<'PY'
import json
import requests
from pathlib import Path

token_path = Path("data/token.json")
d = json.load(token_path.open())

env = {}
for line in Path(".env").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        env[k] = v

r = requests.post(
    "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
    auth=(env["EBAY_CLIENT_ID"], env["EBAY_CLIENT_SECRET"]),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "grant_type": "refresh_token",
        "refresh_token": d["refresh_token"],
        "scope": " ".join([
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.account",
        ]),
    },
    timeout=30,
)

out = r.json()

print("HTTP status:", r.status_code)
print("New access token:", "YES" if out.get("access_token") else "NO")
print("Expires in:", out.get("expires_in"))
print("Error:", out.get("error"))
PY
```

Expected:

```text
HTTP status: 200
New access token: YES
Expires in: 7200
Error: None
```

---

# 21. `.gitignore`

The repository should ignore at least:

```gitignore
.env
.env.*
!.env.example
data/token.json
__pycache__/
*.pyc
```

Never commit real credentials or token files.

---

# 22. Repeating this for additional accounts

For each future eBay account, keep the same application architecture but give each account its own credentials and token storage.

Recommended structure:

```text
accounts/
  account-1/
    .env
    data/token.json
  account-2/
    .env
    data/token.json
  account-3/
    .env
    data/token.json
```

Or deploy separate Docker services if stronger isolation is preferred.

For each account:

1. Create or identify the appropriate eBay Developer keyset.
2. Create/configure a RuName.
3. Configure the Accepted/Declined URLs.
4. Set that account's Client ID, Client Secret, and RuName.
5. Authorize the correct Sandbox or Production seller.
6. Save that seller's refresh token separately.
7. Verify `getVersion` returns HTTP 200.
8. Verify the refresh-token flow returns a new access token.

Do not allow one account's refresh token to overwrite another account's token file.

---

# 23. Troubleshooting notes from the first successful build

### `invalid_grant`

Likely causes:

- authorization code expired;
- authorization code was already used;
- code came from the wrong OAuth helper/client;
- RuName/client mismatch.

Authorization codes are short-lived and single-use.

### `Error processing your request` on eBay

The successful workaround was to generate a clean OAuth URL ourselves with:

```text
prompt=login
```

and open it in an Incognito/InPrivate window.

### Docker variables show `MISSING`

Make sure `docker-compose.yml` contains:

```yaml
env_file:
  - .env
```

Then recreate the container:

```bash
docker compose down
docker compose up -d --build
```

### `/app/data` does not exist

Make sure the host folder exists:

```bash
mkdir -p data
chmod 700 data
```

and Compose contains:

```yaml
volumes:
  - ./data:/app/data
```

### Port 80 already in use

Hostinger's Traefik already owns ports 80 and 443. Do not install or start Nginx on the host for this application.

### Callback page only says authorization code received

That means the old `app.py` is still running. Confirm both host and container contain the automatic exchange code:

```bash
grep -n "eBay OAuth Success" app.py
docker exec ebaybay grep -n "eBay OAuth Success" /app/app.py
```

Then rebuild if necessary.

---

# 24. Definition of done

The account is ready when all of the following are true:

```text
[ ] Sandbox/Production keyset created
[ ] Client ID saved securely
[ ] Client Secret saved securely
[ ] RuName configured
[ ] OAuth scopes = sell.inventory + sell.account
[ ] HTTPS callback works
[ ] Correct seller authorized
[ ] Access token received
[ ] Refresh token received
[ ] Refresh token stored persistently
[ ] Refresh-token flow tested
[ ] Inventory getVersion returns HTTP 200
```

At that point OAuth is no longer a blocker and development can continue with inventory locations, business policies, taxonomy, inventory items, offers, and publishing.