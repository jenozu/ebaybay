import requests
from app import create_app
from app.services.ebay.oauth import OAuthError, get_oauth_service


def main():
    app = create_app()
    with app.app_context():
        if app.config["EBAY_ENVIRONMENT"] != "sandbox":
            raise SystemExit("This smoke check is Sandbox-only.")
        try:
            access_token = get_oauth_service().get_access_token()
        except OAuthError as exc:
            raise SystemExit(str(exc)) from exc
        response = requests.get(
            "https://api.sandbox.ebay.com/sell/inventory/v1/getVersion",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=app.config["EBAY_HTTP_TIMEOUT_SECONDS"],
        )

    print("HTTP status:", response.status_code)
    if response.ok:
        print("Inventory API response received.")
    else:
        print("Inventory API request failed")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
