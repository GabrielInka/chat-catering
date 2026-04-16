import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def history_file_path(phone: str) -> Path:
    safe_phone = re.sub(r"[^0-9]", "", str(phone))
    return BASE_DIR / f"history_{safe_phone}.json"


def get_history(phone: str) -> list[dict]:
    file_path = history_file_path(phone)
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_history(phone: str, user_message: str, bot_reply: str) -> None:
    history = get_history(phone)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_reply})
    history_file_path(phone).write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
