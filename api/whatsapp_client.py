from datetime import datetime
from pathlib import Path

import requests

from config import PHONE_NUMBER_ID, REQUEST_TIMEOUT_SECONDS, WHATSAPP_TOKEN

BASE_DIR = Path(__file__).resolve().parent
READ_ERRORS_LOG = BASE_DIR / "read_errors.log"


def _messages_url() -> str:
    return f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"


def send_whatsapp_message(to: str, message: str) -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            _messages_url(),
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        return {
            "ok": response.ok,
            "status": response.status_code,
            "response": response.text,
            "error": "",
        }
    except requests.RequestException as exc:
        return {"ok": False, "status": 0, "response": "", "error": str(exc)}


def mark_whatsapp_message_as_read(message_id: str) -> dict:
    if not message_id:
        return {"ok": False, "status": 0, "response": "", "error": "Missing message_id"}
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            _messages_url(),
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        result = {
            "ok": response.ok,
            "status": response.status_code,
            "response": response.text,
            "error": "",
        }
    except requests.RequestException as exc:
        result = {"ok": False, "status": 0, "response": "", "error": str(exc)}

    if not result["ok"]:
        with READ_ERRORS_LOG.open("a", encoding="utf-8") as fp:
            fp.write(
                f"{datetime.now().isoformat()} ERROR READ: {message_id} | "
                f"{result['error']} | {result['response']}\n"
            )
    return result
