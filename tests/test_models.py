import pytest

from app.models import Listing, ListingStatus


def test_listing_state_machine_allows_expected_transition():
    listing = Listing(sku="X", quantity=1, status=ListingStatus.DRAFT)
    listing.transition_to(ListingStatus.READY)
    assert listing.status == ListingStatus.READY


def test_listing_state_machine_rejects_invalid_transition():
    listing = Listing(sku="X", quantity=1, status=ListingStatus.DRAFT)
    with pytest.raises(ValueError):
        listing.transition_to(ListingStatus.PUBLISHED)
