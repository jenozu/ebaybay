from decimal import Decimal

from app.extensions import db
from app.models import EbayConnection, Listing, ListingImage, ListingStatus


def image(filename="item.jpg", *, status="PENDING"):
    return ListingImage(
        filename=filename,
        original_filename=filename,
        mime_type="image/jpeg",
        size_bytes=100,
        ebay_upload_status=status,
    )


def listing(sku, status, **values):
    defaults = {
        "title": f"Title {sku}",
        "condition": "Used",
        "quantity": 1,
        "final_price": Decimal("25.00"),
        "ebay_category_id": "123",
    }
    defaults.update(values)
    return Listing(sku=sku, status=status, **defaults)


def test_dashboard_renders_real_counts_states_and_listing_details(client, login, app):
    login()
    with app.app_context():
        draft = listing("DRAFT-1", ListingStatus.DRAFT, product_name="Draft fallback")
        draft.title = None
        draft.images.append(image("draft.jpg"))
        ready = listing("READY-1", ListingStatus.READY)
        staged = listing("STAGED-1", ListingStatus.EBAY_STAGED)
        published = listing(
            "LIVE-1",
            ListingStatus.PUBLISHED,
            ebay_listing_url="https://www.ebay.ca/itm/123456",
        )
        failed = listing("FAILED-1", ListingStatus.READY, ebay_inventory_status="FAILED")
        db.session.add_all([draft, ready, staged, published, failed])
        db.session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'data-testid="draft-count">1<' in html
    assert 'data-testid="attention-count">2<' in html
    assert 'data-testid="ready-count">3<' in html
    assert 'data-testid="published-count">1<' in html
    assert "Draft fallback" in html
    assert "READY-1" in html and "EBAY STAGED" in html and "LIVE-1" in html
    assert "$25.00 CAD" in html and "Inventory staging needs review" in html
    assert "/uploads/draft.jpg" in html
    assert 'href="https://www.ebay.ca/itm/123456"' in html
    assert 'aria-label="Primary navigation"' in html
    assert 'href="/dashboard">Dashboard</a>' in html
    assert 'href="/listings/new">New Listing</a>' in html
    assert 'href="/settings/ebay">Settings</a>' in html


def test_dashboard_filters_drafts_ready_published_and_attention(client, login, app):
    login()
    with app.app_context():
        draft = listing("ONLY-DRAFT", ListingStatus.DRAFT)
        draft.images.append(image())
        ready = listing("ONLY-READY", ListingStatus.READY)
        published = listing("ONLY-LIVE", ListingStatus.PUBLISHED)
        failed = listing("ONLY-FAILED", ListingStatus.READY, ebay_publish_status="UNKNOWN")
        db.session.add_all([draft, ready, published, failed])
        db.session.commit()

    cases = {
        "drafts": ("ONLY-DRAFT", ("ONLY-READY", "ONLY-LIVE", "ONLY-FAILED")),
        "ready": ("ONLY-READY", ("ONLY-DRAFT", "ONLY-LIVE")),
        "published": ("ONLY-LIVE", ("ONLY-DRAFT", "ONLY-READY", "ONLY-FAILED")),
        "attention": ("ONLY-FAILED", ("ONLY-DRAFT", "ONLY-LIVE")),
    }
    for selected, (included, excluded) in cases.items():
        html = client.get(f"/dashboard?view={selected}").get_data(as_text=True)
        assert included in html
        assert all(value not in html for value in excluded)

    invalid = client.get("/dashboard?view=not-a-real-filter").get_data(as_text=True)
    assert 'aria-current="page">All</a>' in invalid


def test_needs_attention_covers_incomplete_drafts_and_pipeline_failures(client, login, app):
    login()
    with app.app_context():
        incomplete = Listing(sku="INCOMPLETE", status=ListingStatus.DRAFT, quantity=1)
        image_failed = listing("IMAGE-FAILED", ListingStatus.READY)
        image_failed.images.append(image(status="FAILED"))
        archived = Listing(sku="ARCHIVED", status=ListingStatus.ARCHIVED, quantity=1)
        db.session.add_all([incomplete, image_failed, archived])
        db.session.commit()

    html = client.get("/dashboard?view=attention").get_data(as_text=True)
    assert "INCOMPLETE" in html
    assert "Add photos, title, condition, price, category" in html
    assert "IMAGE-FAILED" in html and "Image upload needs review" in html
    assert "ARCHIVED" not in html


def test_view_on_ebay_requires_published_status_and_saved_url(client, login, app):
    login()
    with app.app_context():
        db.session.add_all([
            listing("DRAFT-WITH-URL", ListingStatus.DRAFT, ebay_listing_url="https://example.test/not-live"),
            listing("LIVE-NO-URL", ListingStatus.PUBLISHED),
            listing("LIVE-WITH-URL", ListingStatus.PUBLISHED, ebay_listing_url="https://www.ebay.ca/itm/789"),
        ])
        db.session.commit()

    html = client.get("/dashboard").get_data(as_text=True)
    assert html.count("View on eBay") == 1
    assert "https://www.ebay.ca/itm/789" in html
    assert "https://example.test/not-live" not in html


def test_dashboard_empty_state(client, login):
    login()
    html = client.get("/dashboard").get_data(as_text=True)
    assert "No listings yet" in html
    assert "+ New Listing" in html
    assert 'data-testid="draft-count">0<' in html


def test_dashboard_uses_cached_connection_health_without_leaking_credentials(client, login, app):
    login()
    with app.app_context():
        connection = EbayConnection(
            environment="sandbox",
            marketplace_id="EBAY_CA",
            status="CONNECTED",
            encrypted_access_token="DO-NOT-RENDER-ACCESS",
            encrypted_refresh_token="DO-NOT-RENDER-REFRESH",
            default_payment_policy_id="pay",
            default_fulfillment_policy_id="fulfill",
            default_return_policy_id="returns",
            default_merchant_location_key="warehouse",
        )
        db.session.add(connection)
        db.session.commit()

    html = client.get("/dashboard").get_data(as_text=True)
    assert "Connected" in html and "Marketplace:</strong> EBAY_CA" in html
    assert "Seller defaults:</strong> Ready" in html
    assert "DO-NOT-RENDER-ACCESS" not in html
    assert "DO-NOT-RENDER-REFRESH" not in html
