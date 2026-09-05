"""Normalized eBay seller-policy and inventory-location retrieval."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import requests

from ...extensions import db
from ...models import EbayConnection, utcnow
from .oauth import OAuthError, get_oauth_service


class AccountServiceError(OAuthError):
    """Safe Account/Inventory API failure with no sensitive response data."""


@dataclass(frozen=True)
class PolicyOption:
    policy_id: str
    name: str
    marketplace_id: str

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class LocationOption:
    merchant_location_key: str
    name: str
    status: str
    selectable: bool

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SellerDefaults:
    payment_policy_id: str | None
    fulfillment_policy_id: str | None
    return_policy_id: str | None
    merchant_location_key: str | None
    marketplace_id: str


class AccountService:
    def __init__(self, config: dict, *, http=None, token_provider=None):
        self.config = config
        self.http = http or requests
        self.token_provider = token_provider or (lambda: get_oauth_service(config).get_access_token())

    @property
    def base_url(self) -> str:
        configured = self.config.get("EBAY_API_BASE")
        if configured:
            return configured.rstrip("/")
        return "https://api.sandbox.ebay.com" if self.config["EBAY_ENVIRONMENT"].lower() == "sandbox" else "https://api.ebay.com"

    @property
    def marketplace_id(self) -> str:
        return self.config["EBAY_MARKETPLACE_ID"]

    def _get(self, path: str, *, params=None) -> dict:
        try:
            response = self.http.get(f"{self.base_url}{path}", headers={"Authorization": f"Bearer {self.token_provider()}", "Accept": "application/json"}, params=params, timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"])
        except requests.RequestException as exc:
            raise AccountServiceError("eBay seller settings could not be retrieved. Try again later.") from exc
        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            raise AccountServiceError("eBay returned an invalid seller-settings response.") from exc
        if not getattr(response, "ok", False):
            raise AccountServiceError("eBay seller settings could not be retrieved. Check the connection and try again.")
        if not isinstance(payload, dict):
            raise AccountServiceError("eBay returned an invalid seller-settings response.")
        return payload

    def _policies(self, path: str, key: str) -> list[PolicyOption]:
        payload = self._get(path, params={"marketplace_id": self.marketplace_id})
        values = payload.get(key, [])
        if not isinstance(values, list):
            raise AccountServiceError("eBay returned invalid seller policy data.")
        options = []
        for item in values:
            policy_id = item.get("paymentPolicyId") or item.get("fulfillmentPolicyId") or item.get("returnPolicyId") if isinstance(item, dict) else None
            name = item.get("name") if isinstance(item, dict) else None
            if isinstance(policy_id, str) and policy_id and isinstance(name, str) and name:
                options.append(PolicyOption(policy_id, name, self.marketplace_id))
        return options

    def payment_policies(self) -> list[PolicyOption]:
        return self._policies("/sell/account/v1/payment_policy", "paymentPolicies")

    def fulfillment_policies(self) -> list[PolicyOption]:
        return self._policies("/sell/account/v1/fulfillment_policy", "fulfillmentPolicies")

    def return_policies(self) -> list[PolicyOption]:
        return self._policies("/sell/account/v1/return_policy", "returnPolicies")

    def inventory_locations(self) -> list[LocationOption]:
        offset, limit, results = 0, 100, []
        while True:
            payload = self._get("/sell/inventory/v1/location", params={"limit": limit, "offset": offset})
            locations = payload.get("locations", [])
            if not isinstance(locations, list):
                raise AccountServiceError("eBay returned invalid inventory-location data.")
            for item in locations:
                if not isinstance(item, dict):
                    continue
                key = item.get("merchantLocationKey")
                if not isinstance(key, str) or not key:
                    continue
                status = str(item.get("merchantLocationStatus") or "ENABLED").upper()
                name = item.get("name") or key
                results.append(LocationOption(key, str(name), status, status == "ENABLED"))
            total = payload.get("total")
            if not isinstance(total, int) or offset + len(locations) >= total or not locations:
                break
            offset += len(locations)
        return results

    def retrieve_all(self) -> dict:
        return {
            "payment_policies": [item.as_dict() for item in self.payment_policies()],
            "fulfillment_policies": [item.as_dict() for item in self.fulfillment_policies()],
            "return_policies": [item.as_dict() for item in self.return_policies()],
            "inventory_locations": [item.as_dict() for item in self.inventory_locations()],
        }


def saved_defaults(config: dict) -> SellerDefaults:
    connection = get_oauth_service(config).connection()
    return SellerDefaults(
        connection.default_payment_policy_id if connection else None,
        connection.default_fulfillment_policy_id if connection else None,
        connection.default_return_policy_id if connection else None,
        connection.default_merchant_location_key if connection else None,
        config["EBAY_MARKETPLACE_ID"],
    )


def cached_options(connection: EbayConnection | None) -> dict:
    return (connection.seller_defaults_cache or {}) if connection else {}


def refresh_cached_options(config: dict, service: AccountService | None = None) -> tuple[EbayConnection, dict]:
    connection = get_oauth_service(config).connection()
    if connection is None or connection.status != "CONNECTED":
        raise AccountServiceError("eBay is disconnected. Connect the seller account in Settings.")
    options = (service or AccountService(config)).retrieve_all()
    connection.seller_defaults_cache = options
    connection.seller_defaults_refreshed_at = utcnow()
    db.session.commit()
    return connection, options


def save_defaults(config: dict, values: dict) -> EbayConnection:
    connection = get_oauth_service(config).connection()
    if connection is None or connection.status != "CONNECTED":
        raise AccountServiceError("eBay is disconnected. Connect the seller account in Settings.")
    options = cached_options(connection)
    mappings = (
        ("payment_policy_id", "payment_policies", "policy_id", "default_payment_policy_id"),
        ("fulfillment_policy_id", "fulfillment_policies", "policy_id", "default_fulfillment_policy_id"),
        ("return_policy_id", "return_policies", "policy_id", "default_return_policy_id"),
        ("merchant_location_key", "inventory_locations", "merchant_location_key", "default_merchant_location_key"),
    )
    for submitted, collection, option_key, field in mappings:
        value = (values.get(submitted) or "").strip()
        allowed = {entry.get(option_key) for entry in options.get(collection, []) if entry.get("selectable", True)}
        if not value or value not in allowed:
            raise AccountServiceError("Select current eBay seller defaults after refreshing the available options.")
        setattr(connection, field, value)
    db.session.commit()
    return connection


def defaults_validation_issues(config: dict) -> list[tuple[str, str]]:
    connection = get_oauth_service(config).connection()
    defaults = saved_defaults(config)
    fields = (("ebay_payment_policy_id", defaults.payment_policy_id, "payment_policies", "policy_id", "payment policy"), ("ebay_fulfillment_policy_id", defaults.fulfillment_policy_id, "fulfillment_policies", "policy_id", "fulfillment policy"), ("ebay_return_policy_id", defaults.return_policy_id, "return_policies", "policy_id", "return policy"), ("ebay_merchant_location_key", defaults.merchant_location_key, "inventory_locations", "merchant_location_key", "inventory location"))
    issues = []
    options = cached_options(connection)
    for field, value, collection, option_key, label in fields:
        if not value:
            issues.append((field, f"Select a default {label} in eBay Settings before approval."))
        elif collection in options and value not in {entry.get(option_key) for entry in options[collection] if entry.get("selectable", True)}:
            issues.append((field, f"The saved default {label} is no longer available. Refresh eBay Settings and select a replacement."))
    return issues
