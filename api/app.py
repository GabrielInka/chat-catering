import json
import logging
from pathlib import Path

from flask import Flask, Response, request

from agent_service import ask_agent
from blocked_contacts import is_blocked_contact
from config import VERIFY_TOKEN, validate_runtime_config
from history import get_history, save_history
from whatsapp_client import mark_whatsapp_message_as_read, send_whatsapp_message

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
LAST_WEBHOOK_LOG = BASE_DIR / "last_webhook_log.json"

# Validate config on import so Railway/Gunicorn fails fast if env vars are missing.
validate_runtime_config()


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

    if not sender or is_blocked_contact(sender):
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

    history = get_history(sender)
    try:
        reply = ask_agent(text, history)
    except Exception as exc:
        logger.exception("Error generating agent reply for sender=%s: %s", sender, exc)
        reply = "Ahora mismo tengo un problema técnico. ¿Puedes escribirme de nuevo en unos minutos?"

    save_history(sender, text, reply)
    send_whatsapp_message(sender, reply)

    return Response("EVENT_RECEIVED", status=200)


@app.get("/health")
def health() -> Response:
    return Response(json.dumps({"ok": True}), mimetype="application/json", status=200)


if __name__ == "__main__":
    validate_runtime_config()
    app.run(host="0.0.0.0", port=8000, debug=True)
