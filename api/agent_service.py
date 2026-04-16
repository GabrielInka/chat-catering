from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_VECTOR_STORE_ID

INSTRUCTIONS = """Actúa como Vera, el bot de atención al cliente de la empresa Catering Barú. Tu función principal es ayudar a los usuarios respondiendo sus dudas y recomendando los menús de nuestros servicios. Tienes acceso a documentos informativos sobre la empresa y sus productos. Responde de manera profesional, cordial y clara, asegurándote de ofrecer siempre información relevante y adecuada sobre Catering Barú y sus menús.

Responde en español en tono profesional y amable usando párrafos breves, asegurándote de adaptar tus respuestas según la consulta del usuario."""

client = OpenAI(api_key=OPENAI_API_KEY)


def _build_input(history: list[dict], user_message: str) -> list[dict]:
    items: list[dict] = []
    # Keep recent history bounded to avoid huge payloads.
    for msg in history[-20:]:
        role = msg.get("role")
        content = str(msg.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            items.append(
                {
                    "role": role,
                    "content": [{"type": "input_text", "text": content}],
                }
            )
    items.append(
        {
            "role": "user",
            "content": [{"type": "input_text", "text": user_message}],
        }
    )
    return items


def ask_agent(user_message: str, history: list[dict]) -> str:
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
        instructions=INSTRUCTIONS,
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
