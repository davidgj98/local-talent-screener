from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
OFFERS_DIR = DATA_DIR / "offers"


def _ensure_dirs():
    OFFERS_DIR.mkdir(parents=True, exist_ok=True)


def save_offer(data: dict):
    _ensure_dirs()
    path = OFFERS_DIR / f"{data['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def load_offer(offer_id: str) -> dict | None:
    path = OFFERS_DIR / f"{offer_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_offers() -> list[dict]:
    _ensure_dirs()
    offers = []
    for path in sorted(OFFERS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        with open(path, "r", encoding="utf-8") as f:
            offers.append(json.load(f))
    return offers
