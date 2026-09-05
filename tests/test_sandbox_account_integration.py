"""Opt-in verification of Phase 9 defaults against a connected Sandbox seller."""
import os

import pytest

from app.services.ebay.account import AccountService, cached_options, saved_defaults
from app.services.ebay.oauth import get_oauth_service


pytestmark = pytest.mark.skipif(os.getenv("RUN_EBAY_SANDBOX_INTEGRATION") != "1", reason="set RUN_EBAY_SANDBOX_INTEGRATION=1 after Sandbox reauthorization and policy setup")


def test_selected_defaults_match_live_sandbox_resources(app):
    if app.config["EBAY_ENVIRONMENT"] != "sandbox":
        pytest.skip("Sandbox environment is required")
    with app.app_context():
        connection = get_oauth_service().connection()
        assert connection and connection.status == "CONNECTED"
        live = AccountService(app.config).retrieve_all()
        defaults = saved_defaults(app.config)
    assert defaults.payment_policy_id in {item["policy_id"] for item in live["payment_policies"]}
    assert defaults.fulfillment_policy_id in {item["policy_id"] for item in live["fulfillment_policies"]}
    assert defaults.return_policy_id in {item["policy_id"] for item in live["return_policies"]}
    assert defaults.merchant_location_key in {item["merchant_location_key"] for item in live["inventory_locations"] if item["selectable"]}
