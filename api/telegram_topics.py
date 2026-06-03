import json
import logging
import re
from pathlib import Path

import requests

from config import REQUEST_TIMEOUT_SECONDS, TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_CHAT_ID

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TOPICS_FILE = BASE_DIR / "telegram_topics.json"
MAX_TOPICS = 1000


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def _load_topics() -> dict[str, str]:
    if not TOPICS_FILE.exists():
        return {}
    try:
        data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
        phones = data.get("phones")
        if isinstance(phones, dict):
            return {str(k): str(v) for k, v in phones.items()}
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_topics(phones: dict[str, str]) -> None:
    if len(phones) > MAX_TOPICS:
        keys = list(phones.keys())[-MAX_TOPICS:]
        phones = {key: phones[key] for key in keys}
    TOPICS_FILE.write_text(
        json.dumps({"phones": phones}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _topic_name_for_phone(phone: str) -> str:
    safe = re.sub(r"[^0-9+]", "", str(phone)) or str(phone)
    name = f"WA {safe}"
    return name[:128]


def _create_forum_topic(phone: str) -> int | None:
    payload = {
        "chat_id": TELEGRAM_GROUP_CHAT_ID,
        "name": _topic_name_for_phone(phone),
    }
    try:
        response = requests.post(
            _api_url("createForumTopic"),
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        body = response.json() if response.content else {}
        if not response.ok or not body.get("ok"):
            logger.warning("createForumTopic failed for %s: %s", phone, body)
            return None
        thread_id = (body.get("result") or {}).get("message_thread_id")
        return int(thread_id) if thread_id is not None else None
    except requests.RequestException as exc:
        logger.exception("createForumTopic error for %s: %s", phone, exc)
        return None


def get_or_create_topic_id(phone: str) -> int | None:
    if not phone or not TELEGRAM_GROUP_CHAT_ID:
        return None

    topics = _load_topics()
    existing = topics.get(phone)
    if existing:
        try:
            return int(existing)
        except ValueError:
            pass

    thread_id = _create_forum_topic(phone)
    if thread_id is None:
        return None

    topics[phone] = str(thread_id)
    _save_topics(topics)
    return thread_id


def resolve_phone_from_topic(thread_id: int | str | None) -> str:
    if thread_id is None:
        return ""
    thread_str = str(thread_id)
    for phone, stored_thread in _load_topics().items():
        if stored_thread == thread_str:
            return phone
    return ""
