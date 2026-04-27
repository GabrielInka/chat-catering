from pathlib import Path

from openai import OpenAI

from config import (
    AGENT_INSTRUCTIONS,
    AGENT_INSTRUCTIONS_FILE,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_VECTOR_STORE_ID,
)

DEFAULT_INSTRUCTIONS = """Actúa como Vera, el bot de atención al cliente de la empresa Catering Barú. Tu función principal es ayudar a los usuarios respondiendo sus dudas y recomendando los menús de nuestros servicios. Tienes acceso a documentos informativos sobre la empresa y sus productos. Responde de manera profesional, cordial y clara, asegurándote de ofrecer siempre información relevante y adecuada sobre Catering Barú y sus menús.

Responde en español en tono profesional y amable usando párrafos breves, asegurándote de adaptar tus respuestas según la consulta del usuario."""

client = OpenAI(api_key=OPENAI_API_KEY)
BASE_DIR = Path(__file__).resolve().parent


def _resolve_instructions() -> str:
    # Priority:
    # 1) AGENT_INSTRUCTIONS (env plain text)
    # 2) AGENT_INSTRUCTIONS_FILE (path to prompt file)
    # 3) default hardcoded instructions
    env_text = (AGENT_INSTRUCTIONS or "").strip()
    if env_text:
        return env_text

    instructions_file = (AGENT_INSTRUCTIONS_FILE or "").strip()
    if instructions_file:
        path = Path(instructions_file)
        if not path.is_absolute():
            path = (BASE_DIR.parent / path).resolve()
        if path.exists():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
    return DEFAULT_INSTRUCTIONS


def _build_input(history: list[dict], user_message: str) -> list[dict]:
    items: list[dict] = []
    # Keep recent history bounded to avoid huge payloads.
    for msg in history[-20:]:
        role = msg.get("role")
        content = str(msg.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            items.append({"role": role, "content": content})
    items.append({"role": "user", "content": user_message})
    return items


def ask_agent(user_message: str, history: list[dict]) -> str:
    is_first_turn = len(history) == 0
    runtime_rule = (
        'Es el primer mensaje de la conversación: abre con "Hola 👋 Soy Vera, asistente virtual de Catering Barú."'
        if is_first_turn
        else (
            "NO repitas el saludo inicial 'Hola 👋 Soy Vera, asistente virtual de Catering Barú.' "
            "porque ya fue enviado en un turno anterior. "
            "En este turno tampoco uses saludos alternativos como: Hola, Hola de nuevo, Buenas, "
            "Buenos días, Buenas tardes, Buenas noches. Responde directamente siguiendo el flujo."
        )
    )

    tools = []
    if OPENAI_VECTOR_STORE_ID:
        tools.append(
            {
                "type": "file_search",
                "vector_store_ids": [OPENAI_VECTOR_STORE_ID],
            }
        )
    response = client.responses.create(
        model=OPENAI_MODEL,
        input=_build_input(history, user_message),
        instructions=f"{_resolve_instructions()}\n\nRegla de turno actual:\n- {runtime_rule}",
        tools=tools,
        temperature=0.2,
    )
    text = (response.output_text or "").strip()
    if text:
        return text
    return (
        "Ahora mismo no pude generar una respuesta válida. "
        "¿Puedes volver a intentarlo en unos segundos?"
    )
