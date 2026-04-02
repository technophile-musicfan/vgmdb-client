import pytest


@pytest.fixture
def url():
    """Return the url for a drama cd"""
    return {
        "path": "album/8078",
        "catalog_number": "JDCA-29194",
        "barcode": "4988707291944",
        "album_id": 8078
    }

