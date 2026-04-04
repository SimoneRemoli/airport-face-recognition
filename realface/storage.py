import json
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FACES_DIR = DATA_DIR / "faces"
DB_PATH = DATA_DIR / "face_db.json"


def ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    FACES_DIR.mkdir(exist_ok=True)


def load_database() -> List[Dict]:
    ensure_storage()
    if not DB_PATH.exists():
        return []
    with DB_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_database(records: List[Dict]) -> None:
    ensure_storage()
    with DB_PATH.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)


def upsert_person(name: str, descriptor: List[float], sample_path: str) -> None:
    records = load_database()
    existing = next((item for item in records if item["name"].lower() == name.lower()), None)
    if existing:
        existing["name"] = name
        existing["descriptor"] = descriptor
        existing["sample_path"] = sample_path
    else:
        records.append({
            "name": name,
            "descriptor": descriptor,
            "sample_path": sample_path,
        })
    save_database(records)
