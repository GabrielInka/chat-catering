import json
import logging
from pathlib import Path

from flask import Flask, Response, request

from agent_service import ask_agent
from allowed_contacts import is_allowed_contact
from blocked_contacts import is_blocked_contact
from config import (
    TELEGRAM_ENABLED,
    TELEGRAM_WEBHOOK_SECRET,
    VERA_ALLOWLIST_ONLY,
    VERIFY_TOKEN,
    get_telegram_allowed_user_ids,
    is_telegram_forum_mode,
    validate_runtime_config,
)
from history import append_assistant_message, get_history, save_history
from human_pause import is_human_paused, set_human_pause
from telegram_client import (
    get_telegram_destination_chat_id,
    is_telegram_enabled,
    mirror_whatsapp_ai_reply,
    mirror_whatsapp_inbound,
    mirror_whatsapp_paused,
    send_telegram_message,
)
from telegram_routes import register_telegram_message, resolve_phone_from_telegram_reply
from telegram_topics import resolve_phone_from_topic
from whatsapp_client import mark_whatsapp_message_as_read, send_whatsapp_message

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
LAST_WEBHOOK_LOG = BASE_DIR / "last_webhook_log.json"

validate_runtime_config()


def _register_mirror_route(result: dict, phone: str) -> None:
    if result.get("ok") and result.get("message_id") is not None:
        register_telegram_message(result["message_id"], phone)


def _should_process_whatsapp_sender(sender: str) -> bool:
    if not sender or is_blocked_contact(sender):
        return False
    if VERA_ALLOWLIST_ONLY and not is_allowed_contact(sender):
        logger.info("Contacto no autorizado en modo pruebas: %s", sender)
        return False
    return True


def _mirror_inbound_to_telegram(sender: str, text: str, paused: bool) -> None:
    if not is_telegram_enabled():
        return
    if paused:
        result = mirror_whatsapp_paused(sender, text)
    else:
        result = mirror_whatsapp_inbound(sender, text)
    _register_mirror_route(result, sender)


def _is_allowed_telegram_chat(chat_id: str) -> bool:
    if not chat_id:
        return False
    return chat_id == str(get_telegram_destination_chat_id())


def _is_allowed_telegram_user(user_id: str) -> bool:
    allowed = get_telegram_allowed_user_ids()
    if is_telegram_forum_mode():
        return user_id in allowed
    return not allowed or user_id in allowed


def _resolve_phone_from_telegram_message(message: dict) -> str:
    thread_id = message.get("message_thread_id")
    if is_telegram_forum_mode() and thread_id is not None:
        phone = resolve_phone_from_topic(thread_id)
        if phone:
            return phone

    reply_to = message.get("reply_to_message") or {}
    return resolve_phone_from_telegram_reply(reply_to.get("message_id"))


@app.get("/whatsapp-webhook")
def verify_webhook() -> Response:
    mode = request.args.get("hub.mode", request.args.get("hub_mode", ""))
    token = request.args.get("hub.verify_token", request.args.get("hub_verify_token", ""))
    challenge = request.args.get("hub.challenge", request.args.get("hub_challenge", ""))

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(challenge, status=200)
    return Response("Token de verificación inválido", status=403)


@app.post("/whatsapp-webhook")
def receive_whatsapp_message() -> Response:
    raw_body = request.get_data(as_text=True) or ""
    LAST_WEBHOOK_LOG.write_text(raw_body, encoding="utf-8")
    data = request.get_json(silent=True) or {}

    message = (
        data.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("messages", [None])[0]
    )
    if not message:
        return Response("EVENT_RECEIVED", status=200)

    sender = (message.get("from") or "").strip()
    message_type = (message.get("type") or "").strip()
    message_id = (message.get("id") or "").strip()
    if message_id:
        mark_whatsapp_message_as_read(message_id)

    if not _should_process_whatsapp_sender(sender):
        return Response("EVENT_RECEIVED", status=200)

    if message_type != "text":
        send_whatsapp_message(
            sender,
            "Por ahora solo puedo responder mensajes de texto. ¿En qué puedo ayudarte con el catering?",
        )
        return Response("EVENT_RECEIVED", status=200)

    text = ((message.get("text") or {}).get("body") or "").strip()
    if not text:
        return Response("EVENT_RECEIVED", status=200)

    paused = is_human_paused(sender)
    _mirror_inbound_to_telegram(sender, text, paused)

    if paused:
        logger.info("Pausa humana activa para %s; no se llama a la IA", sender)
        return Response("EVENT_RECEIVED", status=200)

    history = get_history(sender)
    try:
        reply = ask_agent(text, history)
    except Exception as exc:
        logger.exception("Error generating agent reply for sender=%s: %s", sender, exc)
        reply = "Ahora mismo tengo un problema técnico. ¿Puedes escribirme de nuevo en unos minutos?"

    save_history(sender, text, reply)
    send_whatsapp_message(sender, reply)

    if is_telegram_enabled():
        result = mirror_whatsapp_ai_reply(sender, reply)
        _register_mirror_route(result, sender)

    return Response("EVENT_RECEIVED", status=200)


def _telegram_webhook_authorized() -> bool:
    if not TELEGRAM_WEBHOOK_SECRET:
        return True
    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return header_secret == TELEGRAM_WEBHOOK_SECRET


@app.post("/telegram-webhook")
def receive_telegram_message() -> Response:
    if not TELEGRAM_ENABLED:
        return Response("OK", status=200)

    if not _telegram_webhook_authorized():
        logger.warning("Telegram webhook: secret_token no coincide o falta cabecera")
        return Response("Unauthorized", status=403)

    data = request.get_json(silent=True) or {}
    message = data.get("message") or data.get("edited_message")
    if not message:
        return Response("OK", status=200)

    chat_id = str((message.get("chat") or {}).get("id", ""))
    if not _is_allowed_telegram_chat(chat_id):
        logger.info("Telegram: chat_id no autorizado %s", chat_id)
        return Response("OK", status=200)

    user_id = str((message.get("from") or {}).get("id", ""))
    if not _is_allowed_telegram_user(user_id):
        logger.info("Telegram: usuario no autorizado %s", user_id)
        return Response("OK", status=200)

    text = (message.get("text") or "").strip()
    if not text or text.startswith("/"):
        return Response("OK", status=200)

    phone = _resolve_phone_from_telegram_message(message)
    thread_id = message.get("message_thread_id")

    if not phone:
        hint = (
            "Escribe dentro del tema del cliente (WA …)."
            if is_telegram_forum_mode()
            else "Usa «Responder» sobre un mensaje espejado del bot."
        )
        send_telegram_message(f"No identifiqué el contacto de WhatsApp. {hint}")
        return Response("OK", status=200)

    if not _should_process_whatsapp_sender(phone):
        send_telegram_message(
            f"No se puede enviar a {phone} (bloqueado o no autorizado).",
            phone=phone if is_telegram_forum_mode() else None,
            thread_id=int(thread_id) if thread_id is not None else None,
        )
        return Response("OK", status=200)

    result = send_whatsapp_message(phone, text)
    if not result.get("ok"):
        logger.warning("Error enviando a WhatsApp desde Telegram: %s", result)
        send_telegram_message(
            "Error al enviar el mensaje a WhatsApp. Revisa los logs del servidor.",
            phone=phone if is_telegram_forum_mode() else None,
            thread_id=int(thread_id) if thread_id is not None else None,
        )
        return Response("OK", status=200)

    set_human_pause(phone)
    append_assistant_message(phone, text)
    send_telegram_message(
        "✅ Enviado a WhatsApp. IA en pausa.",
        phone=phone if is_telegram_forum_mode() else None,
        thread_id=int(thread_id) if thread_id is not None else None,
    )
    return Response("OK", status=200)


@app.get("/health")
def health() -> Response:
    mode = "disabled"
    if is_telegram_enabled():
        mode = "group_forum" if is_telegram_forum_mode() else "private_chat"
    payload = {
        "ok": True,
        "telegram_enabled": is_telegram_enabled(),
        "telegram_mode": mode,
    }
    return Response(json.dumps(payload), mimetype="application/json", status=200)


if __name__ == "__main__":
    validate_runtime_config()
    app.run(host="0.0.0.0", port=8000, debug=True)
