import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROUTES_FILE = BASE_DIR / "telegram_routes.json"
MAX_ROUTES = 500


def _load_routes() -> dict[str, str]:
    if not ROUTES_FILE.exists():
        return {}
    try:
        data = json.loads(ROUTES_FILE.read_text(encoding="utf-8"))
        routes = data.get("routes")
        if isinstance(routes, dict):
            return {str(k): str(v) for k, v in routes.items()}
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_routes(routes: dict[str, str]) -> None:
    if len(routes) > MAX_ROUTES:
        keys = list(routes.keys())[-MAX_ROUTES:]
        routes = {key: routes[key] for key in keys}
    ROUTES_FILE.write_text(
        json.dumps({"routes": routes}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def register_telegram_message(telegram_message_id: int | str | None, phone: str) -> None:
    if telegram_message_id is None or not phone:
        return
    routes = _load_routes()
    routes[str(telegram_message_id)] = phone
    _save_routes(routes)


def resolve_phone_from_telegram_reply(reply_to_message_id: int | str | None) -> str:
    if reply_to_message_id is None:
        return ""
    return _load_routes().get(str(reply_to_message_id), "")
