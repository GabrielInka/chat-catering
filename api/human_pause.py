import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import HUMAN_PAUSE_MINUTES

BASE_DIR = Path(__file__).resolve().parent
PAUSE_FILE = BASE_DIR / "human_pause.json"


def _load_pauses() -> dict[str, str]:
    if not PAUSE_FILE.exists():
        return {}
    try:
        data = json.loads(PAUSE_FILE.read_text(encoding="utf-8"))
        phones = data.get("phones")
        if isinstance(phones, dict):
            return {str(k): str(v) for k, v in phones.items()}
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_pauses(phones: dict[str, str]) -> None:
    PAUSE_FILE.write_text(
        json.dumps({"phones": phones}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _prune_expired(pauses: dict[str, str]) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    active: dict[str, str] = {}
    for phone, expires_raw in pauses.items():
        try:
            expires_at = datetime.fromisoformat(expires_raw)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if expires_at > now:
            active[phone] = expires_raw
    return active


def set_human_pause(phone: str) -> None:
    if not phone:
        return
    pauses = _prune_expired(_load_pauses())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=HUMAN_PAUSE_MINUTES)
    pauses[phone] = expires_at.isoformat()
    _save_pauses(pauses)


def is_human_paused(phone: str) -> bool:
    if not phone:
        return False
    pauses = _prune_expired(_load_pauses())
    if pauses != _load_pauses():
        _save_pauses(pauses)
    return phone in pauses
