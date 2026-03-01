-- ============================================================
-- SUPABASE SETUP - TaskFlow / organizadorBWS
-- Pegar esto en: Supabase > SQL Editor > New Query > Run
-- ============================================================

-- ── Tabla: miembros ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS miembros (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT '',
    color TEXT DEFAULT '#2563eb',
    orden INTEGER DEFAULT 0,
    superior_id INTEGER REFERENCES miembros(id),
    discord_canal_id TEXT,
    activo INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ── Tabla: tareas ───────────────────────────────────────────
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
);

-- ── Tabla: conversaciones ───────────────────────────────────
CREATE TABLE IF NOT EXISTS conversaciones (
    id SERIAL PRIMARY KEY,
    canal_id TEXT NOT NULL,
    rol TEXT NOT NULL,
    mensaje_usuario TEXT NOT NULL,
    respuesta_bot TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- ── Tabla: estados ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS estados (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#71717a',
    orden INTEGER DEFAULT 0,
    es_completado INTEGER DEFAULT 0,
    es_sistema INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1
);

-- ── Tabla: prioridades ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS prioridades (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#71717a',
    orden INTEGER DEFAULT 0,
    es_sistema INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1
);

-- ── Tabla: categorias ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#71717a',
    es_sistema INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1
);

-- ── Tabla: periodos_tiempo ──────────────────────────────────
CREATE TABLE IF NOT EXISTS periodos_tiempo (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    dias_desde INTEGER NOT NULL DEFAULT 0,
    dias_hasta INTEGER NOT NULL DEFAULT 0,
    es_sistema INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1
);


-- ============================================================
-- DATOS INICIALES (Seeds)
-- ============================================================

-- Miembros
INSERT INTO miembros (nombre, rol, color, orden, superior_id, activo, created_at, updated_at) VALUES
    ('Alex Gutierrez', 'CEO', '#f59e0b', 1, NULL, 1, NOW()::TEXT, NOW()::TEXT),
    ('Alex Silvestre', 'CTO', '#2563eb', 2, 1, 1, NOW()::TEXT, NOW()::TEXT);

-- Estados
INSERT INTO estados (nombre, color, orden, es_completado, es_sistema, activo) VALUES
    ('Backlog',        '#71717a', 0, 0, 1, 1),
    ('Por hacer',      '#3b82f6', 1, 0, 1, 1),
    ('En progreso',    '#f59e0b', 2, 0, 1, 1),
    ('Hecho',          '#22c55e', 3, 1, 1, 1),
    ('Por Recuperar',  '#ef4444', 4, 0, 1, 1);

-- Prioridades
INSERT INTO prioridades (nombre, color, orden, es_sistema, activo) VALUES
    ('Alta',  '#ef4444', 0, 1, 1),
    ('Media', '#f59e0b', 1, 1, 1),
    ('Baja',  '#22c55e', 2, 1, 1);

-- Categorias
INSERT INTO categorias (nombre, color, es_sistema, activo) VALUES
    ('Trabajo',  '#3b82f6', 1, 1),
    ('Personal', '#8b5cf6', 1, 1),
    ('Proyecto', '#06b6d4', 1, 1),
    ('Urgente',  '#ef4444', 1, 1);

-- Periodos de tiempo
INSERT INTO periodos_tiempo (nombre, dias_desde, dias_hasta, es_sistema, activo) VALUES
    ('Hoy',          0, 0,  1, 1),
    ('Manana',       1, 1,  1, 1),
    ('Esta semana',  0, 6,  1, 1),
    ('Este mes',     0, 29, 1, 1);
