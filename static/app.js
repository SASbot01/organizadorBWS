const API = '/api';
let currentFilter = 'todas';
let currentPerson = '';
let currentPeriodo = '';
let currentView = 'tasks';

// Dynamic config loaded from API
let CONFIG = {
    miembros: [],
    estados: [],
    prioridades: [],
    categorias: [],
    periodos: [],
};

// ── Elementos ────────────────────────────────────────────
const $tasks = document.getElementById('tasks-container');
const $loading = document.getElementById('loading');
const $empty = document.getElementById('empty-state');
const $input = document.getElementById('input-tarea');
const $btnAdd = document.getElementById('btn-add');
const $btnTheme = document.getElementById('btn-theme');
const $modal = document.getElementById('modal-overlay');

// ── Theme ────────────────────────────────────────────────
function initTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

function isDarkTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
}

$btnTheme.addEventListener('click', () => {
    const dark = isDarkTheme();
    document.documentElement.setAttribute('data-theme', dark ? 'light' : 'dark');
    localStorage.setItem('theme', dark ? 'light' : 'dark');
    // Notify dashboard to re-render charts with new theme
    if (currentView === 'dashboard' && typeof renderDashboard === 'function') {
        renderDashboard();
    }
});

// ── Router ───────────────────────────────────────────────
function initRouter() {
    window.addEventListener('hashchange', handleRoute);
    handleRoute();
}

function handleRoute() {
    const hash = location.hash.replace('#', '') || 'tasks';
    navigateTo(hash, false);
}

function navigateTo(view, pushHash = true) {
    currentView = view;
    if (pushHash) location.hash = view;

    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Show/hide sections
    document.querySelectorAll('.view').forEach(section => {
        section.style.display = 'none';
    });
    const target = document.getElementById(`view-${view}`);
    if (target) target.style.display = 'block';

    // Adjust container width
    const $app = document.getElementById('app-container');
    if (view === 'tasks') {
        $app.classList.remove('wide');
        $app.classList.add('narrow');
    } else {
        $app.classList.remove('narrow');
        $app.classList.add('wide');
    }

    // Trigger view-specific render
    if (view === 'tasks') renderAll();
    else if (view === 'dashboard' && typeof renderDashboard === 'function') renderDashboard();
    else if (view === 'management' && typeof renderManagement === 'function') renderManagement();
}

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => navigateTo(btn.dataset.view));
});

// ── Load Config ──────────────────────────────────────────
async function loadConfig() {
    try {
        const [miembrosRes, estadosRes, prioridadesRes, categoriasRes, periodosRes] = await Promise.all([
            fetch(`${API}/miembros`).then(r => r.json()),
            fetch(`${API}/config/estados`).then(r => r.json()),
            fetch(`${API}/config/prioridades`).then(r => r.json()),
            fetch(`${API}/config/categorias`).then(r => r.json()),
            fetch(`${API}/config/periodos`).then(r => r.json()),
        ]);
        CONFIG.miembros = miembrosRes.miembros || [];
        CONFIG.estados = estadosRes.estados || [];
        CONFIG.prioridades = prioridadesRes.prioridades || [];
        CONFIG.categorias = categoriasRes.categorias || [];
        CONFIG.periodos = periodosRes.periodos || [];
    } catch (e) {
        console.error('Error loading config:', e);
    }

    buildPersonTabs();
    buildFilterPills();
    buildModalSelects();
    buildStatsBar();
}

// ── Build Person Tabs ────────────────────────────────────
function buildPersonTabs() {
    const $container = document.getElementById('person-tabs');
    $container.innerHTML = '';

    // "Todos" tab
    const allBtn = document.createElement('button');
    allBtn.className = 'person-tab active';
    allBtn.dataset.person = '';
    allBtn.textContent = 'Todos';
    allBtn.addEventListener('click', () => selectPerson(allBtn));
    $container.appendChild(allBtn);

    CONFIG.miembros.forEach(m => {
        const btn = document.createElement('button');
        btn.className = 'person-tab';
        const displayName = `${m.nombre} (${m.rol})`;
        btn.dataset.person = displayName;
        btn.innerHTML = `${esc(m.nombre)} <span class="role-tag" style="background:${m.color}20;color:${m.color}">${esc(m.rol)}</span>`;
        btn.addEventListener('click', () => selectPerson(btn));
        $container.appendChild(btn);
    });
}

function selectPerson(btn) {
    document.querySelectorAll('.person-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentPerson = btn.dataset.person;
    recargar();
}

// ── Build Filter Pills ───────────────────────────────────
function buildFilterPills() {
    const $estadoContainer = document.getElementById('estado-filters');
    $estadoContainer.innerHTML = '';

    // "Todas" filter
    const allBtn = document.createElement('button');
    allBtn.className = 'filter active';
    allBtn.dataset.filter = 'todas';
    allBtn.textContent = 'Todas';
    allBtn.addEventListener('click', () => selectEstadoFilter(allBtn));
    $estadoContainer.appendChild(allBtn);

    CONFIG.estados.forEach(e => {
        const btn = document.createElement('button');
        btn.className = 'filter';
        btn.dataset.filter = e.nombre;
        btn.innerHTML = `<span class="filter-dot" style="background:${e.color}"></span>${esc(e.nombre)}`;
        btn.addEventListener('click', () => selectEstadoFilter(btn));
        $estadoContainer.appendChild(btn);
    });

    // Period filters
    const $periodoContainer = document.getElementById('periodo-filters');
    $periodoContainer.innerHTML = '';

    const allPeriodoBtn = document.createElement('button');
    allPeriodoBtn.className = 'filter active';
    allPeriodoBtn.dataset.periodo = '';
    allPeriodoBtn.textContent = 'Todo el tiempo';
    allPeriodoBtn.addEventListener('click', () => selectPeriodoFilter(allPeriodoBtn));
    $periodoContainer.appendChild(allPeriodoBtn);

    CONFIG.periodos.forEach(p => {
        const btn = document.createElement('button');
        btn.className = 'filter';
        btn.dataset.periodo = p.nombre;
        btn.textContent = p.nombre;
        btn.addEventListener('click', () => selectPeriodoFilter(btn));
        $periodoContainer.appendChild(btn);
    });
}

function selectEstadoFilter(btn) {
    document.querySelectorAll('#estado-filters .filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    recargar();
}

function selectPeriodoFilter(btn) {
    document.querySelectorAll('#periodo-filters .filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentPeriodo = btn.dataset.periodo;
    recargar();
}

// ── Build Modal Selects ──────────────────────────────────
function buildModalSelects() {
    // Estado
    const $estado = document.getElementById('edit-estado');
    $estado.innerHTML = '';
    CONFIG.estados.filter(e => e.nombre !== 'Por Recuperar').forEach(e => {
        const opt = document.createElement('option');
        opt.value = e.nombre;
        opt.textContent = e.nombre;
        $estado.appendChild(opt);
    });

    // Prioridad
    const $prioridad = document.getElementById('edit-prioridad');
    $prioridad.innerHTML = '';
    CONFIG.prioridades.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.nombre;
        opt.textContent = p.nombre;
        $prioridad.appendChild(opt);
    });

    // Categoria
    const $categoria = document.getElementById('edit-categoria');
    $categoria.innerHTML = '';
    CONFIG.categorias.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.nombre;
        opt.textContent = c.nombre;
        $categoria.appendChild(opt);
    });

    // Asignado a
    const $asignado = document.getElementById('edit-asignado');
    $asignado.innerHTML = '';
    CONFIG.miembros.forEach(m => {
        const opt = document.createElement('option');
        opt.value = `${m.nombre} (${m.rol})`;
        opt.textContent = `${m.nombre} (${m.rol})`;
        $asignado.appendChild(opt);
    });
    const sinAsignar = document.createElement('option');
    sinAsignar.value = 'Sin asignar';
    sinAsignar.textContent = 'Sin asignar';
    $asignado.appendChild(sinAsignar);
}

// ── Build Stats Bar ──────────────────────────────────────
function buildStatsBar() {
    const $bar = document.getElementById('stats-bar');
    $bar.innerHTML = '';

    // Show key stats: Pendientes, En progreso, Hechas, Vencidas
    const statsDef = [
        { id: 'stat-pendiente', label: 'Pendientes', key: 'por_hacer' },
        { id: 'stat-progreso', label: 'En progreso', key: 'en_progreso' },
        { id: 'stat-hecho', label: 'Hechas', key: 'hecho' },
        { id: 'stat-vencidas', label: 'Vencidas', key: 'por_recuperar' },
    ];

    statsDef.forEach(s => {
        const div = document.createElement('div');
        div.className = 'stat';
        if (s.key === 'por_recuperar') div.classList.add('stat-danger');
        div.innerHTML = `<span class="stat-num" id="${s.id}">0</span><span class="stat-label">${s.label}</span>`;
        $bar.appendChild(div);
    });
}

// ── API calls ────────────────────────────────────────────
async function fetchTareas(filtro, persona, periodo) {
    const params = new URLSearchParams();
    if (filtro && filtro !== 'todas') params.set('estado', filtro);
    if (persona) params.set('asignado_a', persona);
    if (periodo) params.set('periodo', periodo);
    const qs = params.toString();
    const res = await fetch(`${API}/tareas${qs ? '?' + qs : ''}`);
    const data = await res.json();
    return data.tareas || [];
}

async function crearTareaIA(texto) {
    const res = await fetch(`${API}/agente`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: texto, origen: 'Web' }),
    });
    return res.json();
}

async function actualizarTarea(id, datos) {
    const res = await fetch(`${API}/tareas/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos),
    });
    return res.json();
}

async function eliminarTarea(id) {
    const res = await fetch(`${API}/tareas/${id}`, { method: 'DELETE' });
    return res.json();
}

async function fetchStats(persona) {
    const qs = persona ? `?asignado_a=${encodeURIComponent(persona)}` : '';
    const res = await fetch(`${API}/stats${qs}`);
    const data = await res.json();
    return data.stats;
}

// ── Render ───────────────────────────────────────────────
function isOverdue(t) {
    if (!t.fecha_limite || t.estado === 'Hecho') return false;
    return t.fecha_limite < new Date().toISOString().split('T')[0];
}

function renderTarea(t) {
    const isDone = t.estado === 'Hecho';
    const overdue = isOverdue(t);
    const card = document.createElement('div');
    card.className = `task-card${isDone ? ' done' : ''}${overdue ? ' overdue' : ''}`;

    const personaTag = !currentPerson && t.asignado_a && t.asignado_a !== 'Sin asignar'
        ? `<span class="tag tag-persona">${esc(t.asignado_a)}</span>`
        : '';

    const overdueTag = overdue ? '<span class="tag tag-vencida">Vencida</span>' : '';

    // Find priority color from config
    const prioConfig = CONFIG.prioridades.find(p => p.nombre === t.prioridad);
    const prioColor = prioConfig ? prioConfig.color : '#71717a';

    card.innerHTML = `
        <div class="priority-dot" style="background:${prioColor}"></div>
        <div class="task-check${isDone ? ' checked' : ''}" data-id="${t.id}"></div>
        <div class="task-body" data-id="${t.id}">
            <div class="task-title">${esc(t.titulo)}</div>
            ${t.descripcion ? `<div class="task-desc">${esc(t.descripcion)}</div>` : ''}
            <div class="task-meta">
                ${personaTag}
                <span class="tag" style="background:${prioColor}15;color:${prioColor}">${t.prioridad}</span>
                <span class="tag tag-categoria">${t.categoria}</span>
                ${t.origen !== 'Manual' ? `<span class="tag tag-origen">${t.origen}</span>` : ''}
                ${t.fecha_limite ? `<span class="tag tag-fecha">${t.fecha_limite}</span>` : ''}
                ${overdueTag}
            </div>
        </div>
    `;

    // Find completed state
    const completedState = CONFIG.estados.find(e => e.es_completado === 1);
    const doneLabel = completedState ? completedState.nombre : 'Hecho';

    card.querySelector('.task-check').addEventListener('click', async (e) => {
        e.stopPropagation();
        const nuevoEstado = isDone ? 'Por hacer' : doneLabel;
        await actualizarTarea(t.id, { estado: nuevoEstado });
        recargar();
    });

    card.querySelector('.task-body').addEventListener('click', () => abrirModal(t));

    return card;
}

async function renderAll() {
    if (currentView !== 'tasks') return;

    $loading.style.display = 'block';
    $empty.style.display = 'none';

    const [tareas, st] = await Promise.all([
        fetchTareas(currentFilter, currentPerson, currentPeriodo),
        fetchStats(currentPerson),
    ]);

    $loading.style.display = 'none';
    $tasks.querySelectorAll('.task-card').forEach(c => c.remove());

    if (tareas.length === 0) {
        $empty.style.display = 'block';
    } else {
        tareas.forEach(t => $tasks.appendChild(renderTarea(t)));
    }

    // Update stats
    const $pendiente = document.getElementById('stat-pendiente');
    const $progreso = document.getElementById('stat-progreso');
    const $hecho = document.getElementById('stat-hecho');
    const $vencidas = document.getElementById('stat-vencidas');

    if ($pendiente) $pendiente.textContent = st.por_hacer || 0;
    if ($progreso) $progreso.textContent = st.en_progreso || 0;
    if ($hecho) $hecho.textContent = st.hecho || 0;
    if ($vencidas) $vencidas.textContent = st.por_recuperar || 0;
}

function recargar() { renderAll(); }

// ── Quick Add con IA ─────────────────────────────────────
async function addTarea() {
    const texto = $input.value.trim();
    if (!texto) return;

    $btnAdd.disabled = true;
    $input.disabled = true;
    $input.value = 'Procesando con IA...';

    try {
        await crearTareaIA(texto);
        $input.value = '';
        recargar();
    } catch (err) {
        console.error(err);
        alert('Error creando tarea');
        $input.value = texto;
    } finally {
        $btnAdd.disabled = false;
        $input.disabled = false;
        $input.focus();
    }
}

$btnAdd.addEventListener('click', addTarea);
$input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addTarea();
});

// ── Modal ────────────────────────────────────────────────
function abrirModal(t) {
    document.getElementById('edit-id').value = t.id;
    document.getElementById('edit-titulo').value = t.titulo;
    document.getElementById('edit-descripcion').value = t.descripcion || '';
    document.getElementById('edit-estado').value = t.estado;
    document.getElementById('edit-prioridad').value = t.prioridad;
    document.getElementById('edit-categoria').value = t.categoria;
    document.getElementById('edit-asignado').value = t.asignado_a || 'Sin asignar';
    document.getElementById('edit-fecha').value = t.fecha_limite || '';
    $modal.classList.add('open');
}

function cerrarModal() { $modal.classList.remove('open'); }

document.getElementById('btn-close-modal').addEventListener('click', cerrarModal);
$modal.addEventListener('click', (e) => { if (e.target === $modal) cerrarModal(); });

document.getElementById('btn-save').addEventListener('click', async () => {
    const id = document.getElementById('edit-id').value;
    await actualizarTarea(id, {
        titulo: document.getElementById('edit-titulo').value,
        descripcion: document.getElementById('edit-descripcion').value,
        estado: document.getElementById('edit-estado').value,
        prioridad: document.getElementById('edit-prioridad').value,
        categoria: document.getElementById('edit-categoria').value,
        asignado_a: document.getElementById('edit-asignado').value,
        fecha_limite: document.getElementById('edit-fecha').value || null,
    });
    cerrarModal();
    recargar();
});

document.getElementById('btn-delete').addEventListener('click', async () => {
    const id = document.getElementById('edit-id').value;
    if (confirm('Eliminar esta tarea?')) {
        await eliminarTarea(id);
        cerrarModal();
        recargar();
    }
});

// ── Utils ────────────────────────────────────────────────
function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// ── Auto-refresh cada 30s ────────────────────────────────
setInterval(() => {
    if (currentView === 'tasks') recargar();
}, 30000);

// ── Init ─────────────────────────────────────────────────
initTheme();
loadConfig().then(() => {
    initRouter();
});
