import logging

import requests

from config import (
    REQUEST_TIMEOUT_SECONDS,
    TELEGRAM_ADMIN_CHAT_ID,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ENABLED,
)

logger = logging.getLogger(__name__)


def is_telegram_enabled() -> bool:
    return TELEGRAM_ENABLED and bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_ADMIN_CHAT_ID)


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def send_telegram_message(text: str) -> dict:
    if not is_telegram_enabled():
        return {"ok": False, "message_id": None, "error": "Telegram disabled"}

    payload = {
        "chat_id": TELEGRAM_ADMIN_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    try:
        response = requests.post(
            _api_url("sendMessage"),
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        body = response.json() if response.content else {}
        ok = response.ok and body.get("ok") is True
        message_id = None
        if ok:
            message_id = (body.get("result") or {}).get("message_id")
        else:
            logger.warning("Telegram sendMessage failed: %s", body)
        return {
            "ok": ok,
            "message_id": message_id,
            "error": "" if ok else str(body),
        }
    except requests.RequestException as exc:
        logger.exception("Telegram sendMessage error: %s", exc)
        return {"ok": False, "message_id": None, "error": str(exc)}


def mirror_whatsapp_inbound(phone: str, text: str) -> dict:
    body = (
        "📱 Nuevo mensaje de WhatsApp\n"
        f"👤 Usuario: {phone}\n\n"
        f"💬 {text}"
    )
    return send_telegram_message(body)


def mirror_whatsapp_ai_reply(phone: str, text: str) -> dict:
    body = (
        "🤖 [IA] Respuesta enviada a WhatsApp\n"
        f"👤 Usuario: {phone}\n\n"
        f"💬 {text}"
    )
    return send_telegram_message(body)


def mirror_whatsapp_paused(phone: str, text: str) -> dict:
    body = (
        "⏸ Pausa humana activa — sin respuesta automática\n"
        f"👤 Usuario: {phone}\n\n"
        f"💬 {text}\n\n"
        "Responde a este mensaje en Telegram para contestar por WhatsApp."
    )
    return send_telegram_message(body)
