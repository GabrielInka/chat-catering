import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ALLOWED_CONTACTS_FILE = BASE_DIR / "allowed_contacts.json"


def normalize_phone_number(phone: str) -> str:
    return re.sub(r"[^0-9]", "", str(phone))


def get_allowed_contacts_data() -> dict:
    if not ALLOWED_CONTACTS_FILE.exists():
        return {"phones": {}}
    try:
        data = json.loads(ALLOWED_CONTACTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"phones": {}}
    phones = data.get("phones")
    return {"phones": phones if isinstance(phones, dict) else {}}


def is_allowed_contact(phone: str) -> bool:
    normalized = normalize_phone_number(phone)
    if not normalized:
        return False
    return bool(get_allowed_contacts_data()["phones"].get(normalized))
