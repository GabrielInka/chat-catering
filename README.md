# Catering Chat Demo (Python)

Migración del webhook de WhatsApp a Python con integración OpenAI para responder con Vera.

## Requisitos

- Python 3.10+ (en Plesk se usa un `venv` propio, sin tocar el Python global)
- HTTPS público para recibir webhook de Meta

## Configuración local rápida

1. Copia `.env.example` a `.env`.
2. Rellena tus credenciales reales.
3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecuta:

```bash
python api/app.py
```

Endpoints:

- `GET /whatsapp-webhook` (verificación de Meta)
- `POST /whatsapp-webhook` (mensajes entrantes)
- `GET /health` (health check)

## Despliegue en Plesk (con Python 3.10 en venv)

### 1) Subir proyecto

Sube el proyecto al `document root` (o a un subdirectorio de tu dominio).

### 2) Crear `.env`

En la raíz del proyecto, crea el archivo `.env` con las variables de `.env.example`.

### 3) Crear entorno virtual con Python 3.10

Si Plesk no te deja cambiar la versión global, crea tu propio entorno virtual usando el binario 3.10 disponible en el servidor:

```bash
chmod +x scripts/setup_venv_py310.sh
./scripts/setup_venv_py310.sh /ruta/absoluta/a/python3.10
```

Ejemplo típico (depende del servidor):

```bash
./scripts/setup_venv_py310.sh /opt/alt/python310/bin/python3.10
```

Esto crea `.venv310` e instala `requirements.txt`.

### 4) Configurar aplicación Python en Plesk

En **Plesk > Websites & Domains > Python**:

- **Application root**: raíz del proyecto
- **Application startup file**: `passenger_wsgi.py`
- **Application Entry point**: `application`
- **Passenger log file**: el que prefieras para depuración

El archivo `passenger_wsgi.py` ya está preparado para arrancar la app Flask.

### 5) Vincular el venv creado

En la configuración de Python de Plesk, selecciona el intérprete del venv:

- `.../tu_proyecto/.venv310/bin/python`

Si no aparece en UI, deja el de Plesk y añade en variables de entorno:

- `PYTHONHOME` apuntando al venv (si tu hosting lo permite)

### 6) Reiniciar aplicación

Pulsa **Restart App** en Plesk tras cualquier cambio.

## Estructura y notas

- `passenger_wsgi.py`: entrypoint para Plesk/Passenger.
- `api/history_<telefono>.json`: historial por contacto.
- `api/blocked_contacts.json`: bloqueo de contactos.
- `OPENAI_VECTOR_STORE_ID`: activa `file_search` con tu base documental.

## Despliegue en Railway

Si tu Plesk no soporta Python web, Railway es la mejor opción para este proyecto.

### 1) Subir repositorio a GitHub

Sube este proyecto completo a un repositorio (incluyendo `Procfile` y `requirements.txt`).

### 2) Crear proyecto en Railway

1. Entra en Railway.
2. `New Project` -> `Deploy from GitHub repo`.
3. Selecciona tu repositorio.

Railway detectará Python e instalará dependencias de `requirements.txt`.
El arranque usa `Procfile`:

```txt
web: gunicorn --chdir api app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### 3) Configurar Variables de Entorno en Railway

En `Project -> Variables`, añade:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (ejemplo: `gpt-5.4-mini`)
- `OPENAI_VECTOR_STORE_ID` (tu vector store)
- `AGENT_INSTRUCTIONS` (opcional, prompt inline)
- `AGENT_INSTRUCTIONS_FILE` (opcional, ejemplo: `api/agent_instructions.md`)
- `WHATSAPP_TOKEN`
- `PHONE_NUMBER_ID`
- `VERIFY_TOKEN`
- `REQUEST_TIMEOUT_SECONDS` (ejemplo: `25`)

### 4) Obtener URL pública

En Railway, abre tu servicio y copia el dominio generado (por ejemplo `https://tuapp.up.railway.app`).

### 5) Probar servicio

Prueba:

- `GET https://tuapp.up.railway.app/health` -> debe devolver `{"ok": true}`

### 6) Configurar Webhook en Meta

En Meta WhatsApp Cloud API:

- **Callback URL**: `https://tuapp.up.railway.app/whatsapp-webhook`
- **Verify token**: el mismo valor que `VERIFY_TOKEN`

Después suscribe el campo de mensajes (`messages`) en tu app de Meta.

## Personalizar respuestas del agente

Puedes cambiar el comportamiento sin tocar la lógica de código:

- Opción 1: editar `api/agent_instructions.md`.
- Opción 2: definir `AGENT_INSTRUCTIONS` en variables de entorno (Railway).

Orden de prioridad al arrancar:
1. `AGENT_INSTRUCTIONS` (si tiene contenido)
2. `AGENT_INSTRUCTIONS_FILE` (si apunta a un archivo válido)
3. Prompt por defecto embebido en código

Recomendación: en Railway usa `AGENT_INSTRUCTIONS_FILE=api/agent_instructions.md` y versiona ese archivo en Git.
