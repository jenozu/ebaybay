"""Opt-in live smoke test for the main application's OAuth service.

Set RUN_EBAY_SANDBOX_INTEGRATION=1 only after completing the browser consent
flow in Settings with Sandbox credentials. Normal tests never contact eBay.
"""
import os

import pytest
import requests

from app.services.ebay.oauth import get_oauth_service


pytestmark = pytest.mark.skipif(os.getenv("RUN_EBAY_SANDBOX_INTEGRATION") != "1", reason="set RUN_EBAY_SANDBOX_INTEGRATION=1 for live Sandbox OAuth smoke test")


def test_main_app_oauth_service_can_call_sandbox_inventory(app):
    if app.config["EBAY_ENVIRONMENT"] != "sandbox":
        pytest.skip("Sandbox environment is required")
    with app.app_context():
        token = get_oauth_service().get_access_token()
        response = requests.get("https://api.sandbox.ebay.com/sell/inventory/v1/getVersion", headers={"Authorization": f"Bearer {token}"}, timeout=app.config["EBAY_HTTP_TIMEOUT_SECONDS"])
    assert response.status_code == 200
