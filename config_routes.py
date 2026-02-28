from fastapi import APIRouter
from pydantic import BaseModel
from database import (
    listar_estados, crear_estado, actualizar_estado, eliminar_estado,
    listar_prioridades, crear_prioridad, actualizar_prioridad, eliminar_prioridad,
    listar_categorias, crear_categoria, actualizar_categoria, eliminar_categoria,
    listar_periodos, crear_periodo, actualizar_periodo, eliminar_periodo,
)

router = APIRouter(prefix="/api/config", tags=["config"])


# ── Modelos ──────────────────────────────────────────────

class EstadoCreate(BaseModel):
    nombre: str
    color: str = "#71717a"
    orden: int = 0
    es_completado: int = 0

class EstadoUpdate(BaseModel):
    nombre: str | None = None
    color: str | None = None
    orden: int | None = None
    es_completado: int | None = None

class PrioridadCreate(BaseModel):
    nombre: str
    color: str = "#71717a"
    orden: int = 0

class PrioridadUpdate(BaseModel):
    nombre: str | None = None
    color: str | None = None
    orden: int | None = None

class CategoriaCreate(BaseModel):
    nombre: str
    color: str = "#71717a"

class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    color: str | None = None

class PeriodoCreate(BaseModel):
    nombre: str
    dias_desde: int = 0
    dias_hasta: int = 0

class PeriodoUpdate(BaseModel):
    nombre: str | None = None
    dias_desde: int | None = None
    dias_hasta: int | None = None


# ── Estados ──────────────────────────────────────────────

@router.get("/estados")
async def api_listar_estados():
    return {"ok": True, "estados": await listar_estados()}

@router.post("/estados")
async def api_crear_estado(data: EstadoCreate):
    item = await crear_estado(**data.model_dump())
    return {"ok": True, "estado": item}

@router.put("/estados/{item_id}")
async def api_actualizar_estado(item_id: int, data: EstadoUpdate):
    campos = {k: v for k, v in data.model_dump().items() if v is not None}
    if not campos:
        return {"ok": False, "error": "Sin campos"}
    item = await actualizar_estado(item_id, **campos)
    return {"ok": True, "estado": item}

@router.delete("/estados/{item_id}")
async def api_eliminar_estado(item_id: int):
    ok = await eliminar_estado(item_id)
    if not ok:
        return {"ok": False, "error": "No se puede eliminar (es_sistema)"}
    return {"ok": True}


# ── Prioridades ──────────────────────────────────────────

@router.get("/prioridades")
async def api_listar_prioridades():
    return {"ok": True, "prioridades": await listar_prioridades()}

@router.post("/prioridades")
async def api_crear_prioridad(data: PrioridadCreate):
    item = await crear_prioridad(**data.model_dump())
    return {"ok": True, "prioridad": item}

@router.put("/prioridades/{item_id}")
async def api_actualizar_prioridad(item_id: int, data: PrioridadUpdate):
    campos = {k: v for k, v in data.model_dump().items() if v is not None}
    if not campos:
        return {"ok": False, "error": "Sin campos"}
    item = await actualizar_prioridad(item_id, **campos)
    return {"ok": True, "prioridad": item}

@router.delete("/prioridades/{item_id}")
async def api_eliminar_prioridad(item_id: int):
    ok = await eliminar_prioridad(item_id)
    if not ok:
        return {"ok": False, "error": "No se puede eliminar (es_sistema)"}
    return {"ok": True}


# ── Categorias ───────────────────────────────────────────

@router.get("/categorias")
async def api_listar_categorias():
    return {"ok": True, "categorias": await listar_categorias()}

@router.post("/categorias")
async def api_crear_categoria(data: CategoriaCreate):
    item = await crear_categoria(**data.model_dump())
    return {"ok": True, "categoria": item}

@router.put("/categorias/{item_id}")
async def api_actualizar_categoria(item_id: int, data: CategoriaUpdate):
    campos = {k: v for k, v in data.model_dump().items() if v is not None}
    if not campos:
        return {"ok": False, "error": "Sin campos"}
    item = await actualizar_categoria(item_id, **campos)
    return {"ok": True, "categoria": item}

@router.delete("/categorias/{item_id}")
async def api_eliminar_categoria(item_id: int):
    ok = await eliminar_categoria(item_id)
    if not ok:
        return {"ok": False, "error": "No se puede eliminar (es_sistema)"}
    return {"ok": True}


# ── Periodos ─────────────────────────────────────────────

@router.get("/periodos")
async def api_listar_periodos():
    return {"ok": True, "periodos": await listar_periodos()}

@router.post("/periodos")
async def api_crear_periodo(data: PeriodoCreate):
    item = await crear_periodo(**data.model_dump())
    return {"ok": True, "periodo": item}

@router.put("/periodos/{item_id}")
async def api_actualizar_periodo(item_id: int, data: PeriodoUpdate):
    campos = {k: v for k, v in data.model_dump().items() if v is not None}
    if not campos:
        return {"ok": False, "error": "Sin campos"}
    item = await actualizar_periodo(item_id, **campos)
    return {"ok": True, "periodo": item}

@router.delete("/periodos/{item_id}")
async def api_eliminar_periodo(item_id: int):
    ok = await eliminar_periodo(item_id)
    if not ok:
        return {"ok": False, "error": "No se puede eliminar (es_sistema)"}
    return {"ok": True}
