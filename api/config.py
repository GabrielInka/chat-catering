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
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
HUMAN_PAUSE_MINUTES = int(os.getenv("HUMAN_PAUSE_MINUTES", "30"))


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
        telegram_required = {
            "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
            "TELEGRAM_ADMIN_CHAT_ID": TELEGRAM_ADMIN_CHAT_ID,
        }
        telegram_missing = [key for key, value in telegram_required.items() if not value]
        if telegram_missing:
            joined = ", ".join(telegram_missing)
            raise RuntimeError(
                f"TELEGRAM_ENABLED=true but missing Telegram variables: {joined}"
            )

    if HUMAN_PAUSE_MINUTES < 1:
        raise RuntimeError("HUMAN_PAUSE_MINUTES must be at least 1")
