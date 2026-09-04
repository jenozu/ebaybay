import json
import os

import requests
from flask import Blueprint, current_app, request

bp = Blueprint("oauth", __name__)


@bp.get("/privacy")
def privacy():
    return """
    <h1>Privacy Policy</h1>
    <p>This is a private development application used to authenticate with eBay
    and perform seller-authorized API actions.</p>
    <p>Credentials and OAuth tokens are not intentionally shared with third parties.</p>
    """


@bp.get("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "OAuth callback received, but no authorization code was provided.", 400

    token_endpoint = (
        "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        if current_app.config["EBAY_ENVIRONMENT"] == "sandbox"
        else "https://api.ebay.com/identity/v1/oauth2/token"
    )
    try:
        response = requests.post(
            token_endpoint,
            auth=(current_app.config["EBAY_CLIENT_ID"], current_app.config["EBAY_CLIENT_SECRET"]),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": current_app.config["EBAY_RUNAME"]},
            timeout=30,
        )
        data = response.json()
    except Exception as exc:
        return f"<h1>eBay OAuth Failed</h1><p>Token request failed: {type(exc).__name__}</p>", 500

    if response.ok and data.get("access_token") and data.get("refresh_token"):
        token_path = current_app.config["EBAY_TOKEN_PATH"]
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(json.dumps(data), encoding="utf-8")
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


@bp.get("/oauth/declined")
def oauth_declined():
    return "<h1>eBay authorization declined</h1><p>The seller did not grant access.</p>"
