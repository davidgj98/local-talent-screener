from __future__ import annotations

import json
from pathlib import Path

import pytest

from storage import list_offers, load_offer, save_offer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OFFERS_DIR = DATA_DIR / "offers"


@pytest.fixture(autouse=True)
def clean_offers():
    OFFERS_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(OFFERS_DIR.glob("*.json"))
    for p in existing:
        p.unlink()
    yield
    for p in OFFERS_DIR.glob("*.json"):
        p.unlink()


class TestStorage:
    def test_save_and_load(self):
        data = {"id": "test123", "title": "Test Offer", "status": "abierta"}
        save_offer(data)
        loaded = load_offer("test123")
        assert loaded is not None
        assert loaded["title"] == "Test Offer"
        assert loaded["status"] == "abierta"

    def test_load_nonexistent(self):
        assert load_offer("nonexistent") is None

    def test_list_offers_empty(self):
        assert list_offers() == []

    def test_list_offers_multiple(self):
        save_offer({"id": "a", "title": "A"})
        save_offer({"id": "b", "title": "B"})
        all_offers = list_offers()
        assert len(all_offers) == 2
        ids = {o["id"] for o in all_offers}
        assert ids == {"a", "b"}

    def test_overwrite_existing(self):
        save_offer({"id": "x", "title": "Original"})
        save_offer({"id": "x", "title": "Updated"})
        loaded = load_offer("x")
        assert loaded["title"] == "Updated"

    def test_persistence_on_disk(self):
        data = {"id": "disk_test", "title": "Disk", "cvs": []}
        save_offer(data)
        path = OFFERS_DIR / "disk_test.json"
        assert path.exists()
        with open(path) as f:
            raw = json.load(f)
        assert raw["title"] == "Disk"
