from flask import Flask, jsonify, request
import json
import os
from pathlib import Path

import requests

app = Flask(__name__)

TOKEN_PATH = Path(os.getenv("EBAY_TOKEN_PATH", "/app/data/token.json"))
TOKEN_ENDPOINT = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"


@app.get("/")
def home():
    return "eBayBay OAuth callback service is running."


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/privacy")
def privacy():
    return """
    <h1>Privacy Policy</h1>
    <p>This is a private development application used to authenticate with eBay
    and perform seller-authorized API actions.</p>
    <p>Credentials and OAuth tokens are not intentionally shared with third parties.</p>
    """


@app.get("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")

    if not code:
        return "OAuth callback received, but no authorization code was provided.", 400

    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            auth=(
                os.environ["EBAY_CLIENT_ID"],
                os.environ["EBAY_CLIENT_SECRET"],
            ),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
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
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(json.dumps(data), encoding="utf-8")
        os.chmod(TOKEN_PATH, 0o600)

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


@app.get("/oauth/declined")
def oauth_declined():
    return """
    <h1>eBay authorization declined</h1>
    <p>The seller did not grant access.</p>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
