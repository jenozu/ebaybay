import pytest

from app.extensions import db
from app.models import EbayConnection
from app.services.ebay.account import AccountService, AccountServiceError, defaults_validation_issues, refresh_cached_locations, refresh_cached_options, save_defaults, saved_defaults
from app.services.ebay.oauth import OAuthService


class Response:
    def __init__(self, body, ok=True): self.body, self.ok = body, ok
    def json(self): return self.body


class Http:
    def __init__(self, responses): self.responses, self.calls = list(responses), []
    def get(self, *args, **kwargs): self.calls.append(("get", args, kwargs)); return self.responses.pop(0)
    def post(self, *args, **kwargs): self.calls.append(("post", args, kwargs)); return self.responses.pop(0)


def responses():
    return [Response({"paymentPolicies": [{"paymentPolicyId": "pay-1", "name": "Payment"}]}), Response({"fulfillmentPolicies": [{"fulfillmentPolicyId": "ship-1", "name": "Shipping"}]}), Response({"returnPolicies": [{"returnPolicyId": "return-1", "name": "Returns"}]}), Response({"locations": [{"merchantLocationKey": "main", "name": "Main shelf", "merchantLocationStatus": "ENABLED"}, {"merchantLocationKey": "off", "name": "Closed", "merchantLocationStatus": "DISABLED"}], "total": 2})]


def connected(app):
    return OAuthService(app.config).save_token_response({"access_token": "access", "refresh_token": "refresh", "expires_in": 7200}, require_refresh=True)


def test_account_service_normalizes_policy_and_location_resources(app):
    with app.app_context():
        http = Http(responses())
        all_options = AccountService(app.config, http=http, token_provider=lambda: "shared-token").retrieve_all()
        assert all_options["payment_policies"] == [{"policy_id": "pay-1", "name": "Payment", "marketplace_id": "EBAY_CA"}]
        assert all_options["inventory_locations"][0]["selectable"] is True
        assert all_options["inventory_locations"][1]["selectable"] is False
        assert [call[1][0] for call in http.calls] == ["https://api.sandbox.ebay.com/sell/account/v1/payment_policy", "https://api.sandbox.ebay.com/sell/account/v1/fulfillment_policy", "https://api.sandbox.ebay.com/sell/account/v1/return_policy", "https://api.sandbox.ebay.com/sell/inventory/v1/location"]
        assert all(call[2]["headers"]["Authorization"] == "Bearer shared-token" for call in http.calls)
        assert http.calls[0][2]["params"] == {"marketplace_id": "EBAY_CA"}


def test_inventory_locations_paginate_and_malformed_or_api_errors_are_safe(app):
    with app.app_context():
        http = Http([Response({"locations": [{"merchantLocationKey": "one", "name": "One"}], "total": 2}), Response({"locations": [{"merchantLocationKey": "two", "name": "Two"}], "total": 2})])
        values = AccountService(app.config, http=http, token_provider=lambda: "token").inventory_locations()
        assert [value.merchant_location_key for value in values] == ["one", "two"]
        assert http.calls[1][2]["params"]["offset"] == 1
        with pytest.raises(AccountServiceError): AccountService(app.config, http=Http([Response({"paymentPolicies": "bad"})]), token_provider=lambda: "token").payment_policies()
        with pytest.raises(AccountServiceError): AccountService(app.config, http=Http([Response({"error": "bad"}, ok=False)]), token_provider=lambda: "token").payment_policies()


def test_create_inventory_location_uses_official_endpoint_and_safe_payload(app):
    with app.app_context():
        http = Http([Response(None)])
        service = AccountService(app.config, http=http, token_provider=lambda: "shared-token")
        key = service.create_inventory_location({
            "merchant_location_key": "main/location",
            "name": "Main Warehouse",
            "address_line1": "123 Test Street",
            "city": "Mississauga",
            "state_or_province": "ON",
            "postal_code": "L5B 1A1",
            "country": "ca",
            "location_type": "WAREHOUSE",
            "enabled": "1",
        })
        assert key == "main/location"
        method, args, kwargs = http.calls[0]
        assert method == "post"
        assert args[0] == "https://api.sandbox.ebay.com/sell/inventory/v1/location/main%2Flocation"
        assert kwargs["headers"]["Authorization"] == "Bearer shared-token"
        assert kwargs["json"] == {
            "name": "Main Warehouse",
            "location": {"address": {"addressLine1": "123 Test Street", "city": "Mississauga", "stateOrProvince": "ON", "postalCode": "L5B 1A1", "country": "CA"}},
            "locationTypes": ["WAREHOUSE"],
            "merchantLocationStatus": "ENABLED",
        }


def test_create_inventory_location_validates_and_refreshes_location_cache(app):
    with app.app_context():
        connection = connected(app)
        connection.seller_defaults_cache = {"payment_policies": [{"policy_id": "keep", "name": "Keep"}]}
        db.session.commit()
        service = AccountService(app.config, http=Http([Response({"locations": [{"merchantLocationKey": "new", "name": "New", "merchantLocationStatus": "ENABLED"}], "total": 1})]), token_provider=lambda: "token")
        _, options = refresh_cached_locations(app.config, service)
        assert options["payment_policies"][0]["policy_id"] == "keep"
        assert options["inventory_locations"] == [{"merchant_location_key": "new", "name": "New", "status": "ENABLED", "selectable": True}]
        assert EbayConnection.query.one().seller_defaults_cache["inventory_locations"][0]["merchant_location_key"] == "new"
        with pytest.raises(AccountServiceError):
            AccountService(app.config, http=Http([]), token_provider=lambda: "token").create_inventory_location({"merchant_location_key": "bad key", "name": "Name", "address_line1": "1 Main", "city": "City", "state_or_province": "ON", "postal_code": "A1A1A1", "country": "CA"})
        with pytest.raises(AccountServiceError):
            AccountService(app.config, http=Http([]), token_provider=lambda: "token").create_inventory_location({"merchant_location_key": "main", "name": "Name", "address_line1": "1 Main", "city": "City", "state_or_province": "ON", "postal_code": "A1A1A1", "country": "CAN"})
        with pytest.raises(AccountServiceError):
            AccountService(app.config, http=Http([]), token_provider=lambda: "token").create_inventory_location({"merchant_location_key": "main", "name": "Name", "address_line1": "1 Main", "city": "City", "state_or_province": "ON", "postal_code": "A1A1A1", "country": "CA", "location_type": "STORE"})


def test_cached_defaults_persist_are_reusable_and_stale_values_block_validation(app):
    with app.app_context():
        connection = connected(app)
        http = Http(responses())
        refresh_cached_options(app.config, AccountService(app.config, http=http, token_provider=lambda: "shared-token"))
        save_defaults(app.config, {"payment_policy_id": "pay-1", "fulfillment_policy_id": "ship-1", "return_policy_id": "return-1", "merchant_location_key": "main"})
        assert saved_defaults(app.config).payment_policy_id == "pay-1"
        assert defaults_validation_issues(app.config) == []
        connection.seller_defaults_cache = {**connection.seller_defaults_cache, "payment_policies": []}
        db.session.commit()
        assert defaults_validation_issues(app.config)[0][0] == "ebay_payment_policy_id"
        with pytest.raises(AccountServiceError): save_defaults(app.config, {"payment_policy_id": "missing", "fulfillment_policy_id": "ship-1", "return_policy_id": "return-1", "merchant_location_key": "main"})


def test_settings_defaults_routes_render_save_and_are_protected(client, login, app, monkeypatch):
    assert client.post("/settings/ebay/defaults").status_code == 302
    assert client.post("/settings/ebay/inventory-locations").status_code == 302
    login()
    with app.app_context():
        connection = connected(app)
        connection.seller_defaults_cache = {"payment_policies": [{"policy_id": "pay", "name": "Pay"}], "fulfillment_policies": [{"policy_id": "ship", "name": "Ship"}], "return_policies": [{"policy_id": "returns", "name": "Returns"}], "inventory_locations": [{"merchant_location_key": "main", "name": "Main", "selectable": True}]}
        db.session.commit()
    page = client.get("/settings/ebay")
    assert b"Default payment policy" in page.data and b"EBAY_CA" in page.data and b"pay" in page.data
    assert b"Create eBay inventory location" in page.data and b"WAREHOUSE" in page.data
    saved = client.post("/settings/ebay/defaults", data={"payment_policy_id": "pay", "fulfillment_policy_id": "ship", "return_policy_id": "returns", "merchant_location_key": "main"}, follow_redirects=True)
    assert b"saved" in saved.data
    with app.app_context(): assert EbayConnection.query.one().default_merchant_location_key == "main"


def test_create_inventory_location_route_calls_service_and_refresh(client, login, app, monkeypatch):
    login()
    with app.app_context(): connected(app)
    captured = {}

    def fake_create(self, values):
        captured.update(values)
        return "new-main"

    def fake_refresh(config, service):
        captured["refreshed"] = True
        return None, {}

    monkeypatch.setattr(AccountService, "create_inventory_location", fake_create)
    monkeypatch.setattr("app.oauth.refresh_cached_locations", fake_refresh)
    response = client.post("/settings/ebay/inventory-locations", data={
        "merchant_location_key": "new-main",
        "name": "New Main",
        "address_line1": "123 Main",
        "city": "Mississauga",
        "state_or_province": "ON",
        "postal_code": "L5B1A1",
        "country": "CA",
        "location_type": "WAREHOUSE",
        "enabled": "1",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"created and refreshed" in response.data
    assert captured["merchant_location_key"] == "new-main" and captured["refreshed"] is True
