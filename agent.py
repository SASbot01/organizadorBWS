import os
import json
from datetime import datetime, timedelta
import anthropic


SYSTEM_PROMPT_TEMPLATE = """Eres un asistente de productividad. Tu trabajo es interpretar mensajes del usuario y extraer la información necesaria para crear tareas.

Dado un mensaje en lenguaje natural, debes devolver SIEMPRE un JSON válido con esta estructura:

{{
  "accion": "crear_tarea" | "listar_tareas" | "mensaje_general",
  "tarea": {{
    "titulo": "título claro y conciso de la tarea",
    "descripcion": "descripción más detallada si la hay",
    "prioridad": {prioridades_validas},
    "fecha_limite": "YYYY-MM-DD" o null,
    "categoria": {categorias_validas},
    "estado": {estados_validos}
  }},
  "respuesta": "mensaje amigable para confirmar al usuario"
}}

Reglas:
- Si el usuario pide crear/agendar/añadir una tarea, usa accion "crear_tarea"
- Si el usuario pregunta qué tareas tiene o quiere ver sus pendientes, usa "listar_tareas"
- Si el mensaje no es sobre tareas, usa "mensaje_general" y responde normalmente en "respuesta"
- Interpreta fechas relativas: "mañana", "el viernes", "la próxima semana", etc.
- La fecha de hoy es: {fecha_hoy}
- Si no se menciona prioridad, pon "Media"
- Si no se menciona categoría, infiere la más apropiada
- Si no se menciona fecha, pon null
- SIEMPRE responde en español
- SOLO devuelve JSON, sin texto adicional ni markdown
"""


async def interpretar_mensaje(mensaje: str) -> dict:
    """Usa Claude para interpretar un mensaje y extraer datos de tarea."""
    from database import listar_estados, listar_prioridades, listar_categorias

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    # Load dynamic config
    try:
        estados = await listar_estados()
        prioridades = await listar_prioridades()
        categorias = await listar_categorias()

        estados_validos = " | ".join(f'"{e["nombre"]}"' for e in estados if e["nombre"] != "Por Recuperar")
        prioridades_validas = " | ".join(f'"{p["nombre"]}"' for p in prioridades)
        categorias_validas = " | ".join(f'"{c["nombre"]}"' for c in categorias)
    except Exception:
        estados_validos = '"Por hacer" | "En progreso" | "Hecho"'
        prioridades_validas = '"Alta" | "Media" | "Baja"'
        categorias_validas = '"Trabajo" | "Personal" | "Proyecto" | "Urgente"'

    system = SYSTEM_PROMPT_TEMPLATE.format(
        fecha_hoy=fecha_hoy,
        estados_validos=estados_validos,
        prioridades_validas=prioridades_validas,
        categorias_validas=categorias_validas,
    )

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": mensaje}],
    )

    texto = response.content[0].text.strip()

    # Limpiar posible markdown
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1]
        if texto.endswith("```"):
            texto = texto[:-3]
        texto = texto.strip()

    return json.loads(texto)
