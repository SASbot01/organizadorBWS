import aiosqlite
import uuid
from datetime import datetime, date, timedelta

DB_PATH = "tareas.db"


async def init_db():
    """Crea las tablas si no existen y ejecuta seeds."""
    async with aiosqlite.connect(DB_PATH) as db:
        # ── Tabla tareas (existente) ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                estado TEXT DEFAULT 'Por hacer',
                prioridad TEXT DEFAULT 'Media',
                categoria TEXT DEFAULT 'Trabajo',
                fecha_limite TEXT,
                origen TEXT DEFAULT 'Manual',
                asignado_a TEXT DEFAULT 'Sin asignar',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # ── Tabla conversaciones (existente) ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canal_id TEXT NOT NULL,
                rol TEXT NOT NULL,
                mensaje_usuario TEXT NOT NULL,
                respuesta_bot TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── Tabla miembros ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS miembros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT '',
                color TEXT DEFAULT '#2563eb',
                orden INTEGER DEFAULT 0,
                superior_id INTEGER,
                discord_canal_id TEXT,
                activo INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (superior_id) REFERENCES miembros(id)
            )
        """)

        # ── Tabla estados ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS estados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#71717a',
                orden INTEGER DEFAULT 0,
                es_completado INTEGER DEFAULT 0,
                es_sistema INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1
            )
        """)

        # ── Tabla prioridades ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS prioridades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#71717a',
                orden INTEGER DEFAULT 0,
                es_sistema INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1
            )
        """)

        # ── Tabla categorias ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#71717a',
                es_sistema INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1
            )
        """)

        # ── Tabla periodos_tiempo ──
        await db.execute("""
            CREATE TABLE IF NOT EXISTS periodos_tiempo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                dias_desde INTEGER NOT NULL DEFAULT 0,
                dias_hasta INTEGER NOT NULL DEFAULT 0,
                es_sistema INTEGER DEFAULT 0,
                activo INTEGER DEFAULT 1
            )
        """)

        # Migracion: columna asignado_a si no existe
        try:
            await db.execute("ALTER TABLE tareas ADD COLUMN asignado_a TEXT DEFAULT 'Sin asignar'")
        except Exception:
            pass

        await db.commit()

        # ── Seeds ──
        await _seed_data(db)


async def _seed_data(db):
    """Inserta datos iniciales si las tablas estan vacias."""
    now = datetime.now().isoformat()

    # Seed miembros
    count = (await (await db.execute("SELECT COUNT(*) FROM miembros")).fetchone())[0]
    if count == 0:
        await db.execute(
            "INSERT INTO miembros (nombre, rol, color, orden, superior_id, activo, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Alex Gutierrez", "CEO", "#f59e0b", 1, None, 1, now, now),
        )
        await db.execute(
            "INSERT INTO miembros (nombre, rol, color, orden, superior_id, activo, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Alex Silvestre", "CTO", "#2563eb", 2, 1, 1, now, now),
        )

    # Seed estados
    count = (await (await db.execute("SELECT COUNT(*) FROM estados")).fetchone())[0]
    if count == 0:
        estados_seed = [
            ("Backlog", "#71717a", 0, 0, 1),
            ("Por hacer", "#3b82f6", 1, 0, 1),
            ("En progreso", "#f59e0b", 2, 0, 1),
            ("Hecho", "#22c55e", 3, 1, 1),
            ("Por Recuperar", "#ef4444", 4, 0, 1),
        ]
        for nombre, color, orden, es_comp, es_sis in estados_seed:
            await db.execute(
                "INSERT INTO estados (nombre, color, orden, es_completado, es_sistema, activo) VALUES (?, ?, ?, ?, ?, 1)",
                (nombre, color, orden, es_comp, es_sis),
            )

    # Seed prioridades
    count = (await (await db.execute("SELECT COUNT(*) FROM prioridades")).fetchone())[0]
    if count == 0:
        prioridades_seed = [
            ("Alta", "#ef4444", 0, 1),
            ("Media", "#f59e0b", 1, 1),
            ("Baja", "#22c55e", 2, 1),
        ]
        for nombre, color, orden, es_sis in prioridades_seed:
            await db.execute(
                "INSERT INTO prioridades (nombre, color, orden, es_sistema, activo) VALUES (?, ?, ?, ?, 1)",
                (nombre, color, orden, es_sis),
            )

    # Seed categorias
    count = (await (await db.execute("SELECT COUNT(*) FROM categorias")).fetchone())[0]
    if count == 0:
        categorias_seed = [
            ("Trabajo", "#3b82f6", 1),
            ("Personal", "#8b5cf6", 1),
            ("Proyecto", "#06b6d4", 1),
            ("Urgente", "#ef4444", 1),
        ]
        for nombre, color, es_sis in categorias_seed:
            await db.execute(
                "INSERT INTO categorias (nombre, color, es_sistema, activo) VALUES (?, ?, ?, 1)",
                (nombre, color, es_sis),
            )

    # Seed periodos_tiempo
    count = (await (await db.execute("SELECT COUNT(*) FROM periodos_tiempo")).fetchone())[0]
    if count == 0:
        periodos_seed = [
            ("Hoy", 0, 0, 1),
            ("Manana", 1, 1, 1),
            ("Esta semana", 0, 6, 1),
            ("Este mes", 0, 29, 1),
        ]
        for nombre, dias_desde, dias_hasta, es_sis in periodos_seed:
            await db.execute(
                "INSERT INTO periodos_tiempo (nombre, dias_desde, dias_hasta, es_sistema, activo) VALUES (?, ?, ?, ?, 1)",
                (nombre, dias_desde, dias_hasta, es_sis),
            )

    await db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAREAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def crear_tarea(
    titulo: str,
    descripcion: str = "",
    estado: str = "Por hacer",
    prioridad: str = "Media",
    categoria: str = "Trabajo",
    fecha_limite: str | None = None,
    origen: str = "Manual",
    asignado_a: str = "Sin asignar",
) -> dict:
    task_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO tareas (id, titulo, descripcion, estado, prioridad, categoria, fecha_limite, origen, asignado_a, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, titulo, descripcion, estado, prioridad, categoria, fecha_limite, origen, asignado_a, now, now),
        )
        await db.commit()

    return {
        "id": task_id,
        "titulo": titulo,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad,
        "categoria": categoria,
        "fecha_limite": fecha_limite,
        "origen": origen,
        "asignado_a": asignado_a,
        "created_at": now,
        "updated_at": now,
    }


async def listar_tareas(
    estado: str | None = None,
    prioridad: str | None = None,
    categoria: str | None = None,
    asignado_a: str | None = None,
    periodo: str | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    limite: int = 50,
) -> list[dict]:
    query = "SELECT * FROM tareas"
    params: list = []
    filtros: list[str] = []

    if estado:
        if estado == "Por Recuperar":
            # Virtual state: overdue tasks that are not completed
            hoy = date.today().isoformat()
            filtros.append("fecha_limite IS NOT NULL")
            filtros.append("fecha_limite < ?")
            params.append(hoy)
            filtros.append("estado != 'Hecho'")
        else:
            filtros.append("estado = ?")
            params.append(estado)

    if prioridad:
        filtros.append("prioridad = ?")
        params.append(prioridad)
    if categoria:
        filtros.append("categoria = ?")
        params.append(categoria)
    if asignado_a:
        filtros.append("asignado_a = ?")
        params.append(asignado_a)

    # Period filter
    if periodo:
        periodo_data = await _obtener_periodo(periodo)
        if periodo_data:
            hoy = date.today()
            f_desde = (hoy + timedelta(days=periodo_data["dias_desde"])).isoformat()
            f_hasta = (hoy + timedelta(days=periodo_data["dias_hasta"])).isoformat()
            filtros.append("fecha_limite IS NOT NULL")
            filtros.append("fecha_limite >= ?")
            params.append(f_desde)
            filtros.append("fecha_limite <= ?")
            params.append(f_hasta)

    # Explicit date range filter
    if fecha_desde:
        filtros.append("fecha_limite IS NOT NULL")
        filtros.append("fecha_limite >= ?")
        params.append(fecha_desde)
    if fecha_hasta:
        filtros.append("fecha_limite IS NOT NULL")
        filtros.append("fecha_limite <= ?")
        params.append(fecha_hasta)

    if filtros:
        query += " WHERE " + " AND ".join(filtros)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limite)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def _obtener_periodo(nombre: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM periodos_tiempo WHERE nombre = ? AND activo = 1", (nombre,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def obtener_tarea(task_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tareas WHERE id = ?", (task_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def actualizar_tarea(task_id: str, **campos) -> dict | None:
    campos["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in campos)
    values = list(campos.values()) + [task_id]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE tareas SET {sets} WHERE id = ?", values)
        await db.commit()

    return await obtener_tarea(task_id)


async def eliminar_tarea(task_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM tareas WHERE id = ?", (task_id,))
        await db.commit()
        return cursor.rowcount > 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONVERSACIONES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def guardar_conversacion(
    canal_id: str,
    rol: str,
    mensaje_usuario: str,
    respuesta_bot: str,
) -> None:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO conversaciones (canal_id, rol, mensaje_usuario, respuesta_bot, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (canal_id, rol, mensaje_usuario, respuesta_bot, now),
        )
        await db.commit()


async def obtener_historial(canal_id: str, limite: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM conversaciones WHERE canal_id = ? ORDER BY created_at DESC LIMIT ?",
            (canal_id, limite),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in reversed(rows)]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STATS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def stats(asignado_a: str | None = None) -> dict:
    """Stats basicas - conteo dinamico basado en tabla estados."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get all active states
        estados_list = await (await db.execute("SELECT nombre, es_completado FROM estados WHERE activo = 1 ORDER BY orden")).fetchall()

        base = "SELECT COUNT(*) FROM tareas"
        filtros: list[str] = []
        params: list = []

        if asignado_a:
            filtros.append("asignado_a = ?")
            params.append(asignado_a)

        def q(extra=None, extra_params=None):
            f = list(filtros)
            p = list(params)
            if extra:
                f.append(extra)
                if extra_params:
                    p.extend(extra_params)
            where = (" WHERE " + " AND ".join(f)) if f else ""
            return base + where, p

        query, p = q()
        total = (await (await db.execute(query, p)).fetchone())[0]

        # Count per state dynamically
        result = {"total": total}
        for row in estados_list:
            nombre = row["nombre"]
            key = nombre.lower().replace(" ", "_")
            if nombre == "Por Recuperar":
                # Virtual: overdue + not completed
                hoy = date.today().isoformat()
                qry, prms = q("fecha_limite IS NOT NULL AND fecha_limite < ? AND estado != 'Hecho'", [hoy])
            else:
                qry, prms = q("estado = ?", [nombre])
            count = (await (await db.execute(qry, prms)).fetchone())[0]
            result[key] = count

        # Backward compatibility keys
        if "por_hacer" not in result:
            result["por_hacer"] = 0
        if "en_progreso" not in result:
            result["en_progreso"] = 0
        if "hecho" not in result:
            result["hecho"] = 0

    return result


async def stats_dashboard(asignado_a: str | None = None) -> dict:
    """Stats completas para el dashboard de analytics."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        base_where = ""
        base_params: list = []
        if asignado_a:
            base_where = " WHERE asignado_a = ?"
            base_params = [asignado_a]

        def add_where(extra, extra_params=None):
            if base_where:
                w = base_where + " AND " + extra
            else:
                w = " WHERE " + extra
            p = list(base_params) + (extra_params or [])
            return w, p

        # Total
        total = (await (await db.execute(f"SELECT COUNT(*) FROM tareas{base_where}", base_params)).fetchone())[0]

        # By state
        by_estado = []
        estados_rows = await (await db.execute("SELECT * FROM estados WHERE activo = 1 ORDER BY orden")).fetchall()
        hoy = date.today().isoformat()
        for e in estados_rows:
            nombre = e["nombre"]
            if nombre == "Por Recuperar":
                w, p = add_where("fecha_limite IS NOT NULL AND fecha_limite < ? AND estado != 'Hecho'", [hoy])
            else:
                w, p = add_where("estado = ?", [nombre])
            count = (await (await db.execute(f"SELECT COUNT(*) FROM tareas{w}", p)).fetchone())[0]
            by_estado.append({"nombre": nombre, "color": e["color"], "count": count})

        # By priority
        by_prioridad = []
        prio_rows = await (await db.execute("SELECT * FROM prioridades WHERE activo = 1 ORDER BY orden")).fetchall()
        for pr in prio_rows:
            w, p = add_where("prioridad = ?", [pr["nombre"]])
            count = (await (await db.execute(f"SELECT COUNT(*) FROM tareas{w}", p)).fetchone())[0]
            by_prioridad.append({"nombre": pr["nombre"], "color": pr["color"], "count": count})

        # By category
        by_categoria = []
        cat_rows = await (await db.execute("SELECT * FROM categorias WHERE activo = 1")).fetchall()
        for c in cat_rows:
            w, p = add_where("categoria = ?", [c["nombre"]])
            count = (await (await db.execute(f"SELECT COUNT(*) FROM tareas{w}", p)).fetchone())[0]
            by_categoria.append({"nombre": c["nombre"], "color": c["color"], "count": count})

        # By person (workload)
        by_persona = []
        miembros_rows = await (await db.execute("SELECT * FROM miembros WHERE activo = 1 ORDER BY orden")).fetchall()
        for m in miembros_rows:
            display_name = f"{m['nombre']} ({m['rol']})"
            persona_where = " WHERE asignado_a = ?"
            persona_params = [display_name]
            if asignado_a:
                persona_where += " AND asignado_a = ?"
                persona_params.append(asignado_a)

            # Count by state for each person
            persona_estados = {}
            for e in estados_rows:
                nombre = e["nombre"]
                if nombre == "Por Recuperar":
                    qry = f"SELECT COUNT(*) FROM tareas{persona_where} AND fecha_limite IS NOT NULL AND fecha_limite < ? AND estado != 'Hecho'"
                    prms = persona_params + [hoy]
                else:
                    qry = f"SELECT COUNT(*) FROM tareas{persona_where} AND estado = ?"
                    prms = persona_params + [nombre]
                cnt = (await (await db.execute(qry, prms)).fetchone())[0]
                persona_estados[nombre] = cnt

            total_persona = (await (await db.execute(f"SELECT COUNT(*) FROM tareas{persona_where}", persona_params)).fetchone())[0]
            by_persona.append({
                "nombre": display_name,
                "color": m["color"],
                "total": total_persona,
                "estados": persona_estados,
            })

        # Timeline: tasks created and completed per day (last 30 days)
        timeline = []
        for i in range(29, -1, -1):
            d = (date.today() - timedelta(days=i)).isoformat()
            # Created on this day
            w_created, p_created = add_where("DATE(created_at) = ?", [d])
            created = (await (await db.execute(f"SELECT COUNT(*) FROM tareas{w_created}", p_created)).fetchone())[0]
            # Completed on this day (updated_at when estado = Hecho)
            w_done, p_done = add_where("estado = 'Hecho' AND DATE(updated_at) = ?", [d])
            done = (await (await db.execute(f"SELECT COUNT(*) FROM tareas{w_done}", p_done)).fetchone())[0]
            timeline.append({"fecha": d, "creadas": created, "completadas": done})

        # Overdue count
        w_overdue, p_overdue = add_where("fecha_limite IS NOT NULL AND fecha_limite < ? AND estado != 'Hecho'", [hoy])
        vencidas = (await (await db.execute(f"SELECT COUNT(*) FROM tareas{w_overdue}", p_overdue)).fetchone())[0]

    return {
        "total": total,
        "vencidas": vencidas,
        "by_estado": by_estado,
        "by_prioridad": by_prioridad,
        "by_categoria": by_categoria,
        "by_persona": by_persona,
        "timeline": timeline,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MIEMBROS (CRUD)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def listar_miembros(activo: bool = True) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM miembros"
        if activo:
            q += " WHERE activo = 1"
        q += " ORDER BY orden"
        rows = await (await db.execute(q)).fetchall()
        return [dict(r) for r in rows]


async def crear_miembro(nombre: str, rol: str = "", color: str = "#2563eb", orden: int = 0, superior_id: int | None = None, discord_canal_id: str | None = None) -> dict:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO miembros (nombre, rol, color, orden, superior_id, discord_canal_id, activo, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (nombre, rol, color, orden, superior_id, discord_canal_id, now, now),
        )
        await db.commit()
        mid = cursor.lastrowid
    return await obtener_miembro(mid)


async def obtener_miembro(miembro_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute("SELECT * FROM miembros WHERE id = ?", (miembro_id,))).fetchone()
        return dict(row) if row else None


async def actualizar_miembro(miembro_id: int, **campos) -> dict | None:
    campos["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in campos)
    values = list(campos.values()) + [miembro_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE miembros SET {sets} WHERE id = ?", values)
        await db.commit()
    return await obtener_miembro(miembro_id)


async def eliminar_miembro(miembro_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM miembros WHERE id = ?", (miembro_id,))
        await db.commit()
        return cursor.rowcount > 0


async def obtener_orgchart() -> list[dict]:
    """Arbol jerarquico desde miembros."""
    miembros = await listar_miembros(activo=True)
    by_id = {m["id"]: {**m, "hijos": []} for m in miembros}
    raices = []
    for m in miembros:
        nodo = by_id[m["id"]]
        if m["superior_id"] and m["superior_id"] in by_id:
            by_id[m["superior_id"]]["hijos"].append(nodo)
        else:
            raices.append(nodo)
    return raices


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIG CRUD (estados, prioridades, categorias, periodos)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def _listar_config(tabla: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        order = "ORDER BY orden" if tabla in ("estados", "prioridades") else "ORDER BY id"
        rows = await (await db.execute(f"SELECT * FROM {tabla} WHERE activo = 1 {order}")).fetchall()
        return [dict(r) for r in rows]


async def _crear_config(tabla: str, **campos) -> dict:
    keys = ", ".join(campos.keys())
    placeholders = ", ".join("?" for _ in campos)
    values = list(campos.values())
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(f"INSERT INTO {tabla} ({keys}) VALUES ({placeholders})", values)
        await db.commit()
        new_id = cursor.lastrowid
        db.row_factory = aiosqlite.Row
        row = await (await db.execute(f"SELECT * FROM {tabla} WHERE id = ?", (new_id,))).fetchone()
        return dict(row)


async def _actualizar_config(tabla: str, item_id: int, **campos) -> dict | None:
    sets = ", ".join(f"{k} = ?" for k in campos)
    values = list(campos.values()) + [item_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE {tabla} SET {sets} WHERE id = ?", values)
        await db.commit()
        db.row_factory = aiosqlite.Row
        row = await (await db.execute(f"SELECT * FROM {tabla} WHERE id = ?", (item_id,))).fetchone()
        return dict(row) if row else None


async def _eliminar_config(tabla: str, item_id: int) -> bool:
    """Solo elimina si no es es_sistema."""
    async with aiosqlite.connect(DB_PATH) as db:
        row = await (await db.execute(f"SELECT es_sistema FROM {tabla} WHERE id = ?", (item_id,))).fetchone()
        if row and row[0] == 1:
            return False
        await db.execute(f"UPDATE {tabla} SET activo = 0 WHERE id = ?", (item_id,))
        await db.commit()
        return True


# Convenience wrappers
async def listar_estados(): return await _listar_config("estados")
async def crear_estado(**c): return await _crear_config("estados", **c)
async def actualizar_estado(id, **c): return await _actualizar_config("estados", id, **c)
async def eliminar_estado(id): return await _eliminar_config("estados", id)

async def listar_prioridades(): return await _listar_config("prioridades")
async def crear_prioridad(**c): return await _crear_config("prioridades", **c)
async def actualizar_prioridad(id, **c): return await _actualizar_config("prioridades", id, **c)
async def eliminar_prioridad(id): return await _eliminar_config("prioridades", id)

async def listar_categorias(): return await _listar_config("categorias")
async def crear_categoria(**c): return await _crear_config("categorias", **c)
async def actualizar_categoria(id, **c): return await _actualizar_config("categorias", id, **c)
async def eliminar_categoria(id): return await _eliminar_config("categorias", id)

async def listar_periodos(): return await _listar_config("periodos_tiempo")
async def crear_periodo(**c): return await _crear_config("periodos_tiempo", **c)
async def actualizar_periodo(id, **c): return await _actualizar_config("periodos_tiempo", id, **c)
async def eliminar_periodo(id): return await _eliminar_config("periodos_tiempo", id)
