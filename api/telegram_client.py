import logging

import requests

from config import (
    REQUEST_TIMEOUT_SECONDS,
    TELEGRAM_ADMIN_CHAT_ID,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ENABLED,
    TELEGRAM_GROUP_CHAT_ID,
    is_telegram_forum_mode,
)
from telegram_topics import get_or_create_topic_id

logger = logging.getLogger(__name__)


def is_telegram_enabled() -> bool:
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN:
        return False
    return bool(TELEGRAM_GROUP_CHAT_ID or TELEGRAM_ADMIN_CHAT_ID)


def get_telegram_destination_chat_id() -> str:
    if TELEGRAM_GROUP_CHAT_ID:
        return TELEGRAM_GROUP_CHAT_ID
    return TELEGRAM_ADMIN_CHAT_ID


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def send_telegram_message(
    text: str,
    *,
    phone: str | None = None,
    thread_id: int | None = None,
) -> dict:
    if not is_telegram_enabled():
        return {"ok": False, "message_id": None, "thread_id": None, "error": "Telegram disabled"}

    chat_id = get_telegram_destination_chat_id()
    resolved_thread_id = thread_id

    if is_telegram_forum_mode() and phone:
        if resolved_thread_id is None:
            resolved_thread_id = get_or_create_topic_id(phone)
        if resolved_thread_id is None:
            return {
                "ok": False,
                "message_id": None,
                "thread_id": None,
                "error": "Could not create forum topic",
            }

    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if resolved_thread_id is not None:
        payload["message_thread_id"] = resolved_thread_id

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
            "thread_id": resolved_thread_id,
            "error": "" if ok else str(body),
        }
    except requests.RequestException as exc:
        logger.exception("Telegram sendMessage error: %s", exc)
        return {"ok": False, "message_id": None, "thread_id": None, "error": str(exc)}


def mirror_whatsapp_inbound(phone: str, text: str) -> dict:
    if is_telegram_forum_mode():
        body = f"📱 Entrante\n\n💬 {text}"
    else:
        body = (
            "📱 Nuevo mensaje de WhatsApp\n"
            f"👤 Usuario: {phone}\n\n"
            f"💬 {text}"
        )
    return send_telegram_message(body, phone=phone)


def mirror_whatsapp_ai_reply(phone: str, text: str) -> dict:
    if is_telegram_forum_mode():
        body = f"🤖 [IA]\n\n💬 {text}"
    else:
        body = (
            "🤖 [IA] Respuesta enviada a WhatsApp\n"
            f"👤 Usuario: {phone}\n\n"
            f"💬 {text}"
        )
    return send_telegram_message(body, phone=phone)


def mirror_whatsapp_paused(phone: str, text: str) -> dict:
    if is_telegram_forum_mode():
        body = (
            f"⏸ Sin respuesta automática\n\n💬 {text}\n\n"
            "Escribe en este tema para contestar por WhatsApp."
        )
    else:
        body = (
            "⏸ Pausa humana activa — sin respuesta automática\n"
            f"👤 Usuario: {phone}\n\n"
            f"💬 {text}\n\n"
            "Responde a este mensaje en Telegram para contestar por WhatsApp."
        )
    return send_telegram_message(body, phone=phone)
