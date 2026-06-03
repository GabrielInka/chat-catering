import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_VECTOR_STORE_ID = os.getenv("OPENAI_VECTOR_STORE_ID", "")
# Opcional: segundo vector store solo con documentación de menús (api/vector_docs/menus/).
OPENAI_VECTOR_STORE_MENUS_ID = os.getenv("OPENAI_VECTOR_STORE_MENUS_ID", "")
AGENT_INSTRUCTIONS = os.getenv("AGENT_INSTRUCTIONS", "")
AGENT_INSTRUCTIONS_FILE = os.getenv("AGENT_INSTRUCTIONS_FILE", "")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")

REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "25"))

# Modo pruebas: si true, VERA solo responde a números en allowed_contacts.json.
VERA_ALLOWLIST_ONLY = os.getenv("VERA_ALLOWLIST_ONLY", "false").lower() == "true"

# Telegram: bandeja del operador (espejo de WhatsApp + respuestas manuales).
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Chat privado (modo legacy). Ignorado si TELEGRAM_GROUP_CHAT_ID está definido.
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
# Supergrupo con Temas activados: un tema por número de WhatsApp.
TELEGRAM_GROUP_CHAT_ID = os.getenv("TELEGRAM_GROUP_CHAT_ID", "")
# IDs de usuario de Telegram que pueden enviar mensajes a WhatsApp (separados por coma).
TELEGRAM_ALLOWED_USER_IDS = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
HUMAN_PAUSE_MINUTES = int(os.getenv("HUMAN_PAUSE_MINUTES", "30"))


def is_telegram_forum_mode() -> bool:
    return bool(TELEGRAM_GROUP_CHAT_ID.strip())


def get_telegram_allowed_user_ids() -> set[str]:
    return {
        part.strip()
        for part in TELEGRAM_ALLOWED_USER_IDS.split(",")
        if part.strip()
    }


def validate_runtime_config() -> None:
    required = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "WHATSAPP_TOKEN": WHATSAPP_TOKEN,
        "PHONE_NUMBER_ID": PHONE_NUMBER_ID,
        "VERIFY_TOKEN": VERIFY_TOKEN,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variables: {joined}")

    if TELEGRAM_ENABLED:
        if not TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_ENABLED=true but missing TELEGRAM_BOT_TOKEN")
        if not TELEGRAM_GROUP_CHAT_ID and not TELEGRAM_ADMIN_CHAT_ID:
            raise RuntimeError(
                "TELEGRAM_ENABLED=true but set TELEGRAM_GROUP_CHAT_ID or TELEGRAM_ADMIN_CHAT_ID"
            )
        if is_telegram_forum_mode() and not get_telegram_allowed_user_ids():
            raise RuntimeError(
                "TELEGRAM_GROUP_CHAT_ID requires TELEGRAM_ALLOWED_USER_IDS "
                "(comma-separated Telegram user IDs)"
            )

    if HUMAN_PAUSE_MINUTES < 1:
        raise RuntimeError("HUMAN_PAUSE_MINUTES must be at least 1")
