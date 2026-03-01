// ── Dashboard View ───────────────────────────────────────
let dashboardCharts = [];

function destroyCharts() {
    dashboardCharts.forEach(c => c.destroy());
    dashboardCharts = [];
}

function chartColors() {
    const dark = isDarkTheme();
    return {
        text: dark ? '#fafafa' : '#18181b',
        textSecondary: dark ? '#a1a1aa' : '#71717a',
        grid: dark ? '#27272a' : '#e4e4e7',
        bg: dark ? '#18181b' : '#ffffff',
    };
}

async function renderDashboard() {
    const $content = document.getElementById('dashboard-content');
    if (!$content) return;

    const qs = currentPerson ? `?asignado_a=${encodeURIComponent(currentPerson)}` : '';
    const res = await fetch(`${API}/stats/dashboard${qs}`);
    const data = await res.json();
    const d = data.dashboard;
    const colors = chartColors();

    destroyCharts();

    // ── Summary Cards ────────────────────────────────────
    const pendientes = d.by_estado.reduce((s, e) => e.nombre !== 'Hecho' && e.nombre !== 'Por Recuperar' ? s + e.count : s, 0);
    const enProgreso = d.by_estado.find(e => e.nombre === 'En progreso');
    const hechas = d.by_estado.find(e => e.nombre === 'Hecho');
    const porRecuperar = d.by_estado.find(e => e.nombre === 'Por Recuperar');

    $content.innerHTML = `
        <div class="dash-summary">
            <div class="dash-card">
                <span class="dash-card-num">${d.total}</span>
                <span class="dash-card-label">Total</span>
            </div>
            <div class="dash-card">
                <span class="dash-card-num">${pendientes}</span>
                <span class="dash-card-label">Pendientes</span>
            </div>
            <div class="dash-card">
                <span class="dash-card-num">${enProgreso ? enProgreso.count : 0}</span>
                <span class="dash-card-label">En progreso</span>
            </div>
            <div class="dash-card">
                <span class="dash-card-num">${hechas ? hechas.count : 0}</span>
                <span class="dash-card-label">Hechas</span>
            </div>
            <div class="dash-card dash-card-danger">
                <span class="dash-card-num">${porRecuperar ? porRecuperar.count : 0}</span>
                <span class="dash-card-label">Por Recuperar</span>
            </div>
        </div>

        <div class="dash-grid">
            <div class="dash-chart-card dash-chart-wide">
                <h3>Tareas creadas vs completadas</h3>
                <canvas id="chart-timeline"></canvas>
            </div>
            <div class="dash-chart-card">
                <h3>Por prioridad</h3>
                <canvas id="chart-priority"></canvas>
            </div>
            <div class="dash-chart-card">
                <h3>Por categoria</h3>
                <canvas id="chart-category"></canvas>
            </div>
            <div class="dash-chart-card dash-chart-wide">
                <h3>Carga por persona</h3>
                <canvas id="chart-workload"></canvas>
            </div>
        </div>
    `;

    // ── Timeline Chart (Line) ────────────────────────────
    const timelineCtx = document.getElementById('chart-timeline').getContext('2d');
    const timelineLabels = d.timeline.map(t => t.fecha.slice(5)); // MM-DD
    dashboardCharts.push(new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: timelineLabels,
            datasets: [
                {
                    label: 'Creadas',
                    data: d.timeline.map(t => t.creadas),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59,130,246,0.1)',
                    fill: true,
                    tension: 0.3,
                },
                {
                    label: 'Completadas',
                    data: d.timeline.map(t => t.completadas),
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34,197,94,0.1)',
                    fill: true,
                    tension: 0.3,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: colors.text } },
            },
            scales: {
                x: { ticks: { color: colors.textSecondary, maxTicksLimit: 10 }, grid: { color: colors.grid } },
                y: { ticks: { color: colors.textSecondary }, grid: { color: colors.grid }, beginAtZero: true },
            },
        },
    }));

    // ── Priority Chart (Bar) ─────────────────────────────
    const prioCtx = document.getElementById('chart-priority').getContext('2d');
    dashboardCharts.push(new Chart(prioCtx, {
        type: 'bar',
        data: {
            labels: d.by_prioridad.map(p => p.nombre),
            datasets: [{
                data: d.by_prioridad.map(p => p.count),
                backgroundColor: d.by_prioridad.map(p => p.color + 'cc'),
                borderColor: d.by_prioridad.map(p => p.color),
                borderWidth: 1,
                borderRadius: 6,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: colors.textSecondary }, grid: { display: false } },
                y: { ticks: { color: colors.textSecondary }, grid: { color: colors.grid }, beginAtZero: true },
            },
        },
    }));

    // ── Category Chart (Donut) ───────────────────────────
    const catCtx = document.getElementById('chart-category').getContext('2d');
    const catData = d.by_categoria.filter(c => c.count > 0);
    dashboardCharts.push(new Chart(catCtx, {
        type: 'doughnut',
        data: {
            labels: catData.map(c => c.nombre),
            datasets: [{
                data: catData.map(c => c.count),
                backgroundColor: catData.map(c => c.color + 'cc'),
                borderColor: colors.bg,
                borderWidth: 3,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: colors.text, padding: 16 },
                },
            },
        },
    }));

    // ── Workload Chart (Stacked Bar) ─────────────────────
    if (d.by_persona.length > 0) {
        const workCtx = document.getElementById('chart-workload').getContext('2d');
        const personLabels = d.by_persona.map(p => p.nombre);
        const estadoNames = d.by_estado.filter(e => e.nombre !== 'Por Recuperar').map(e => e.nombre);

        const datasets = estadoNames.map(nombre => {
            const estado = d.by_estado.find(e => e.nombre === nombre);
            return {
                label: nombre,
                data: d.by_persona.map(p => p.estados[nombre] || 0),
                backgroundColor: (estado ? estado.color : '#71717a') + 'cc',
                borderRadius: 4,
            };
        });

        dashboardCharts.push(new Chart(workCtx, {
            type: 'bar',
            data: { labels: personLabels, datasets },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: colors.text } },
                },
                scales: {
                    x: { stacked: true, ticks: { color: colors.textSecondary }, grid: { display: false } },
                    y: { stacked: true, ticks: { color: colors.textSecondary }, grid: { color: colors.grid }, beginAtZero: true },
                },
            },
        }));
    }
}
