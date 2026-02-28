import os
import json
from datetime import datetime
import anthropic


COACH_SYSTEM_PROMPT = """Eres un coach de productividad experto para equipos tech. Tu rol es ayudar al {rol} a gestionar y ejecutar sus tareas del dia.

CONTEXTO:
- Fecha de hoy: {fecha_hoy}
- Rol del usuario: {rol}
- Tareas pendientes del usuario:
{tareas_texto}

HISTORIAL DE CONVERSACIONES ANTERIORES (para aprender del contexto):
{historial_texto}

TU COMPORTAMIENTO:
1. Cuando el usuario se identifica o pide sus tareas:
   - Muestra un resumen claro de sus tareas pendientes para hoy
   - Prioriza por urgencia y impacto
   - Sugiere por cual empezar y por que

2. Cuando el usuario pregunta "como hago esta tarea?" o "que prompt le meto a Claude?":
   - Analiza la tarea especifica
   - Da pasos concretos y accionables para completarla
   - Si es una tarea que se puede hacer con IA, genera un prompt detallado y listo para copiar/pegar en Claude
   - Si es una tarea que no requiere IA, da un plan de accion paso a paso

3. Cuando el usuario pregunta algo general sobre productividad o su trabajo:
   - Responde con consejos practicos basados en su contexto y tareas
   - Usa el historial para personalizar las respuestas

REGLAS:
- Responde SIEMPRE en espanol
- Se conciso pero util. No rellenes con frases vacias
- Cuando generes prompts para Claude, hazlos especificos y detallados, listos para usar
- Numera los pasos de accion
- Si el usuario menciona una tarea por nombre o numero, refierete a ella de las tareas pendientes
- Aprende del historial: si el usuario ya pregunto por algo, no repitas, avanza
- Adapta tu tono al rol del usuario

FORMATO DE RESPUESTA:
Responde en texto plano (markdown compatible con Discord). NO devuelvas JSON.
"""


async def coach_responder(
    mensaje: str,
    rol: str,
    tareas: list[dict],
    historial: list[dict],
) -> str:
    """Genera una respuesta de coaching basada en el contexto del usuario."""

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    # Formatear tareas
    if tareas:
        lineas = []
        for i, t in enumerate(tareas, 1):
            prio = t.get("prioridad", "Media")
            emoji = {"Alta": "🔴", "Media": "🟡", "Baja": "🟢"}.get(prio, "⚪")
            fecha = f" (limite: {t['fecha_limite']})" if t.get("fecha_limite") else ""
            lineas.append(
                f"  {i}. {emoji} [{prio}] {t.get('titulo', 'Sin titulo')}{fecha}\n"
                f"     Categoria: {t.get('categoria', 'N/A')} | Estado: {t.get('estado', 'N/A')}\n"
                f"     Descripcion: {t.get('descripcion', 'Sin descripcion')}"
            )
        tareas_texto = "\n".join(lineas)
    else:
        tareas_texto = "  (No tiene tareas pendientes)"

    # Formatear historial (ultimas conversaciones para contexto)
    if historial:
        lineas_h = []
        for h in historial[-10:]:  # Ultimas 10 interacciones
            lineas_h.append(f"  Usuario: {h.get('mensaje_usuario', '')}")
            lineas_h.append(f"  Coach: {h.get('respuesta_bot', '')[:200]}...")
        historial_texto = "\n".join(lineas_h)
    else:
        historial_texto = "  (Primera conversacion)"

    system = COACH_SYSTEM_PROMPT.format(
        rol=rol,
        fecha_hoy=fecha_hoy,
        tareas_texto=tareas_texto,
        historial_texto=historial_texto,
    )

    # Construir mensajes con historial reciente de la sesion
    messages = [{"role": "user", "content": mensaje}]

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system,
        messages=messages,
    )

    return response.content[0].text.strip()
