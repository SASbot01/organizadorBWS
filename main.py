from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio
import threading
import logging

load_dotenv()

from database import (
    init_db, crear_tarea, listar_tareas, obtener_tarea, actualizar_tarea, eliminar_tarea,
    stats, stats_dashboard,
    listar_miembros, crear_miembro, obtener_miembro, actualizar_miembro, eliminar_miembro, obtener_orgchart,
    listar_estados, listar_prioridades, listar_categorias, listar_periodos,
)
from agent import interpretar_mensaje
from config_routes import router as config_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TaskFlow - Gestor de Tareas")
app.include_router(config_router)


@app.on_event("startup")
async def startup():
    await init_db()


# ── Frontend ──────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


# ── API REST - Tareas ────────────────────────────────────

class TareaCreate(BaseModel):
    titulo: str
    descripcion: str = ""
    estado: str = "Por hacer"
    prioridad: str = "Media"
    categoria: str = "Trabajo"
    fecha_limite: str | None = None
    origen: str = "Manual"
    asignado_a: str = "Sin asignar"


class TareaUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    estado: str | None = None
    prioridad: str | None = None
    categoria: str | None = None
    fecha_limite: str | None = None
    asignado_a: str | None = None


@app.get("/api/tareas")
async def api_listar_tareas(
    estado: str | None = None,
    prioridad: str | None = None,
    categoria: str | None = None,
    asignado_a: str | None = None,
    periodo: str | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
):
    tareas = await listar_tareas(
        estado=estado, prioridad=prioridad, categoria=categoria,
        asignado_a=asignado_a, periodo=periodo,
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
    )
    return {"ok": True, "tareas": tareas}


@app.post("/api/tareas")
async def api_crear_tarea(tarea: TareaCreate):
    nueva = await crear_tarea(**tarea.model_dump())
    return {"ok": True, "tarea": nueva}


@app.get("/api/tareas/{task_id}")
async def api_obtener_tarea(task_id: str):
    tarea = await obtener_tarea(task_id)
    if not tarea:
        return {"ok": False, "error": "Tarea no encontrada"}
    return {"ok": True, "tarea": tarea}


@app.put("/api/tareas/{task_id}")
async def api_actualizar_tarea(task_id: str, datos: TareaUpdate):
    campos = {k: v for k, v in datos.model_dump().items() if v is not None}
    if not campos:
        return {"ok": False, "error": "Sin campos para actualizar"}
    tarea = await actualizar_tarea(task_id, **campos)
    if not tarea:
        return {"ok": False, "error": "Tarea no encontrada"}
    return {"ok": True, "tarea": tarea}


@app.delete("/api/tareas/{task_id}")
async def api_eliminar_tarea(task_id: str):
    ok = await eliminar_tarea(task_id)
    return {"ok": ok}


# ── Stats ─────────────────────────────────────────────────

@app.get("/api/stats")
async def api_stats(asignado_a: str | None = None):
    data = await stats(asignado_a=asignado_a)
    return {"ok": True, "stats": data}


@app.get("/api/stats/dashboard")
async def api_stats_dashboard(asignado_a: str | None = None):
    data = await stats_dashboard(asignado_a=asignado_a)
    return {"ok": True, "dashboard": data}


# ── Miembros (Team) ──────────────────────────────────────

class MiembroCreate(BaseModel):
    nombre: str
    rol: str = ""
    color: str = "#2563eb"
    orden: int = 0
    superior_id: int | None = None
    discord_canal_id: str | None = None


class MiembroUpdate(BaseModel):
    nombre: str | None = None
    rol: str | None = None
    color: str | None = None
    orden: int | None = None
    superior_id: int | None = None
    discord_canal_id: str | None = None
    activo: int | None = None


@app.get("/api/miembros")
async def api_listar_miembros():
    return {"ok": True, "miembros": await listar_miembros()}


@app.post("/api/miembros")
async def api_crear_miembro(data: MiembroCreate):
    m = await crear_miembro(**data.model_dump())
    return {"ok": True, "miembro": m}


@app.get("/api/miembros/orgchart")
async def api_orgchart():
    return {"ok": True, "orgchart": await obtener_orgchart()}


@app.get("/api/miembros/{miembro_id}")
async def api_obtener_miembro(miembro_id: int):
    m = await obtener_miembro(miembro_id)
    if not m:
        return {"ok": False, "error": "Miembro no encontrado"}
    return {"ok": True, "miembro": m}


@app.put("/api/miembros/{miembro_id}")
async def api_actualizar_miembro(miembro_id: int, data: MiembroUpdate):
    campos = {k: v for k, v in data.model_dump().items() if v is not None}
    if not campos:
        return {"ok": False, "error": "Sin campos"}
    m = await actualizar_miembro(miembro_id, **campos)
    return {"ok": True, "miembro": m}


@app.delete("/api/miembros/{miembro_id}")
async def api_eliminar_miembro(miembro_id: int):
    ok = await eliminar_miembro(miembro_id)
    return {"ok": ok}


# ── Endpoint universal para agentes/bots ─────────────────

class MensajeAgente(BaseModel):
    mensaje: str
    origen: str = "API"


@app.post("/api/agente")
async def api_agente(data: MensajeAgente):
    """Endpoint universal: manda texto natural -> el agente lo interpreta -> crea/lista tareas."""
    resultado = await interpretar_mensaje(data.mensaje)
    accion = resultado.get("accion", "mensaje_general")

    if accion == "crear_tarea":
        tarea_data = resultado.get("tarea", {})
        tarea = await crear_tarea(
            titulo=tarea_data.get("titulo", data.mensaje),
            descripcion=tarea_data.get("descripcion", ""),
            estado=tarea_data.get("estado", "Por hacer"),
            prioridad=tarea_data.get("prioridad", "Media"),
            fecha_limite=tarea_data.get("fecha_limite"),
            categoria=tarea_data.get("categoria", "Trabajo"),
            origen=data.origen,
        )
        return {"ok": True, "accion": "tarea_creada", "tarea": tarea, "respuesta": resultado.get("respuesta")}

    elif accion == "listar_tareas":
        tareas = await listar_tareas(estado="Por hacer")
        return {"ok": True, "accion": "tareas_listadas", "tareas": tareas}

    return {"ok": True, "accion": "mensaje", "respuesta": resultado.get("respuesta", "")}


# ── Arranque ──────────────────────────────────────────────

def start_discord_bot():
    """Arranca el bot de Discord en un hilo separado."""
    from discord_bot import run_bot
    run_bot()


if __name__ == "__main__":
    import uvicorn
    import os

    # Arrancar Discord bot en hilo separado
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    if token and token != "tu_token_de_discord_aqui":
        logger.info("Arrancando bot de Discord...")
        t = threading.Thread(target=start_discord_bot, daemon=True)
        t.start()
    else:
        logger.warning("DISCORD_BOT_TOKEN no configurado. Bot de Discord desactivado.")

    # Arrancar servidor web
    uvicorn.run(app, host="0.0.0.0", port=8000)
