// ── Management View ──────────────────────────────────────
let currentMgmtTab = 'estados';

function renderManagement() {
    const $content = document.getElementById('management-content');
    if (!$content) return;

    $content.innerHTML = `
        <div class="mgmt-tabs">
            <button class="mgmt-tab active" data-tab="estados">Estados</button>
            <button class="mgmt-tab" data-tab="prioridades">Prioridades</button>
            <button class="mgmt-tab" data-tab="categorias">Categorias</button>
            <button class="mgmt-tab" data-tab="periodos">Periodos</button>
            <button class="mgmt-tab" data-tab="equipo">Equipo</button>
            <button class="mgmt-tab" data-tab="organigrama">Organigrama</button>
        </div>
        <div id="mgmt-panel"></div>
    `;

    $content.querySelectorAll('.mgmt-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            $content.querySelectorAll('.mgmt-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMgmtTab = btn.dataset.tab;
            renderMgmtPanel();
        });
    });

    renderMgmtPanel();
}

function renderMgmtPanel() {
    const tab = currentMgmtTab;
    if (tab === 'estados') renderConfigList('estados', 'estados', ['nombre', 'color', 'orden', 'es_completado']);
    else if (tab === 'prioridades') renderConfigList('prioridades', 'prioridades', ['nombre', 'color', 'orden']);
    else if (tab === 'categorias') renderConfigList('categorias', 'categorias', ['nombre', 'color']);
    else if (tab === 'periodos') renderConfigList('periodos', 'periodos', ['nombre', 'dias_desde', 'dias_hasta']);
    else if (tab === 'equipo') renderEquipo();
    else if (tab === 'organigrama') renderOrganigramaView();
}

// ── Generic Config List ──────────────────────────────────
async function renderConfigList(tipo, apiKey, fields) {
    const $panel = document.getElementById('mgmt-panel');
    const res = await fetch(`${API}/config/${tipo}`);
    const data = await res.json();
    const items = data[apiKey] || [];

    let html = `<div class="mgmt-section">`;

    // Form to create new item
    html += `<div class="mgmt-form" id="form-create-${tipo}">
        <h3>Nuevo ${tipo.slice(0, -1)}</h3>
        <div class="mgmt-form-row">`;

    fields.forEach(f => {
        if (f === 'color') {
            html += `<div class="mgmt-field"><label>${f}</label><input type="color" name="${f}" value="#71717a"></div>`;
        } else if (f === 'es_completado') {
            html += `<div class="mgmt-field"><label>Completado?</label><select name="${f}"><option value="0">No</option><option value="1">Si</option></select></div>`;
        } else if (f === 'nombre') {
            html += `<div class="mgmt-field mgmt-field-wide"><label>${f}</label><input type="text" name="${f}" placeholder="Nombre"></div>`;
        } else {
            html += `<div class="mgmt-field"><label>${f}</label><input type="number" name="${f}" value="0"></div>`;
        }
    });

    html += `</div><button class="btn-primary btn-sm" id="btn-create-${tipo}">Crear</button></div>`;

    // List of existing items
    html += `<div class="mgmt-list">`;
    items.forEach(item => {
        const isSistema = item.es_sistema === 1;
        html += `<div class="mgmt-item${isSistema ? ' sistema' : ''}" data-id="${item.id}">
            <div class="mgmt-item-info">
                ${item.color ? `<span class="mgmt-color-dot" style="background:${item.color}"></span>` : ''}
                <span class="mgmt-item-name">${esc(item.nombre)}</span>
                ${isSistema ? '<span class="tag tag-sistema">Sistema</span>' : ''}
                ${item.es_completado === 1 ? '<span class="tag tag-completado">Completado</span>' : ''}
                ${item.dias_desde !== undefined ? `<span class="mgmt-item-detail">Dias: ${item.dias_desde} - ${item.dias_hasta}</span>` : ''}
                ${item.orden !== undefined ? `<span class="mgmt-item-detail">Orden: ${item.orden}</span>` : ''}
            </div>
            <div class="mgmt-item-actions">
                <button class="btn-sm btn-edit" data-id="${item.id}" data-tipo="${tipo}">Editar</button>
                ${!isSistema ? `<button class="btn-sm btn-danger-sm" data-id="${item.id}" data-tipo="${tipo}">Eliminar</button>` : ''}
            </div>
        </div>`;
    });
    html += `</div></div>`;

    $panel.innerHTML = html;

    // Create handler
    document.getElementById(`btn-create-${tipo}`).addEventListener('click', async () => {
        const form = document.getElementById(`form-create-${tipo}`);
        const body = {};
        fields.forEach(f => {
            const input = form.querySelector(`[name="${f}"]`);
            if (f === 'orden' || f === 'dias_desde' || f === 'dias_hasta' || f === 'es_completado') {
                body[f] = parseInt(input.value) || 0;
            } else {
                body[f] = input.value;
            }
        });

        if (!body.nombre || !body.nombre.trim()) { alert('El nombre es requerido'); return; }

        await fetch(`${API}/config/${tipo}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        await loadConfig();
        renderMgmtPanel();
    });

    // Delete handlers
    $panel.querySelectorAll('.btn-danger-sm').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Eliminar este elemento?')) return;
            await fetch(`${API}/config/${btn.dataset.tipo}/${btn.dataset.id}`, { method: 'DELETE' });
            await loadConfig();
            renderMgmtPanel();
        });
    });

    // Edit handlers
    $panel.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            const item = items.find(i => String(i.id) === id);
            if (!item) return;
            openEditConfigModal(tipo, item, fields);
        });
    });
}

// ── Edit Config Modal ────────────────────────────────────
function openEditConfigModal(tipo, item, fields) {
    // Create inline edit form
    const $panel = document.getElementById('mgmt-panel');
    const existing = $panel.querySelector('.mgmt-edit-inline');
    if (existing) existing.remove();

    const $itemEl = $panel.querySelector(`.mgmt-item[data-id="${item.id}"]`);
    if (!$itemEl) return;

    const $form = document.createElement('div');
    $form.className = 'mgmt-edit-inline';
    let inner = '<div class="mgmt-form-row">';

    fields.forEach(f => {
        const val = item[f] ?? '';
        if (f === 'color') {
            inner += `<div class="mgmt-field"><label>${f}</label><input type="color" name="edit-${f}" value="${val}"></div>`;
        } else if (f === 'es_completado') {
            inner += `<div class="mgmt-field"><label>Completado?</label><select name="edit-${f}"><option value="0"${val === 0 ? ' selected' : ''}>No</option><option value="1"${val === 1 ? ' selected' : ''}>Si</option></select></div>`;
        } else if (f === 'nombre') {
            inner += `<div class="mgmt-field mgmt-field-wide"><label>${f}</label><input type="text" name="edit-${f}" value="${esc(String(val))}"></div>`;
        } else {
            inner += `<div class="mgmt-field"><label>${f}</label><input type="number" name="edit-${f}" value="${val}"></div>`;
        }
    });

    inner += `</div><div class="mgmt-edit-actions">
        <button class="btn-primary btn-sm" id="btn-save-edit">Guardar</button>
        <button class="btn-sm" id="btn-cancel-edit">Cancelar</button>
    </div>`;

    $form.innerHTML = inner;
    $itemEl.after($form);

    $form.querySelector('#btn-cancel-edit').addEventListener('click', () => $form.remove());
    $form.querySelector('#btn-save-edit').addEventListener('click', async () => {
        const body = {};
        fields.forEach(f => {
            const input = $form.querySelector(`[name="edit-${f}"]`);
            if (f === 'orden' || f === 'dias_desde' || f === 'dias_hasta' || f === 'es_completado') {
                body[f] = parseInt(input.value) || 0;
            } else {
                body[f] = input.value;
            }
        });

        await fetch(`${API}/config/${tipo}/${item.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        await loadConfig();
        renderMgmtPanel();
    });
}

// ── Equipo (Team Members) ────────────────────────────────
async function renderEquipo() {
    const $panel = document.getElementById('mgmt-panel');
    const res = await fetch(`${API}/miembros`);
    const data = await res.json();
    const miembros = data.miembros || [];

    let superiorOptions = '<option value="">Sin superior</option>';
    miembros.forEach(m => {
        superiorOptions += `<option value="${m.id}">${esc(m.nombre)} (${esc(m.rol)})</option>`;
    });

    let html = `<div class="mgmt-section">
        <div class="mgmt-form" id="form-create-miembro">
            <h3>Nuevo miembro</h3>
            <div class="mgmt-form-row">
                <div class="mgmt-field mgmt-field-wide"><label>Nombre</label><input type="text" name="nombre" placeholder="Nombre completo"></div>
                <div class="mgmt-field"><label>Rol</label><input type="text" name="rol" placeholder="CEO, CTO, Dev..."></div>
                <div class="mgmt-field"><label>Color</label><input type="color" name="color" value="#2563eb"></div>
                <div class="mgmt-field"><label>Orden</label><input type="number" name="orden" value="0"></div>
                <div class="mgmt-field"><label>Superior</label><select name="superior_id">${superiorOptions}</select></div>
                <div class="mgmt-field"><label>Discord Canal ID</label><input type="text" name="discord_canal_id" placeholder="ID del canal"></div>
            </div>
            <button class="btn-primary btn-sm" id="btn-create-miembro">Crear miembro</button>
        </div>

        <div class="mgmt-list">`;

    miembros.forEach(m => {
        const superiorName = m.superior_id ? (miembros.find(s => s.id === m.superior_id)?.nombre || '') : '';
        html += `<div class="mgmt-item" data-id="${m.id}">
            <div class="mgmt-item-info">
                <span class="mgmt-color-dot" style="background:${m.color}"></span>
                <span class="mgmt-item-name">${esc(m.nombre)}</span>
                <span class="tag" style="background:${m.color}20;color:${m.color}">${esc(m.rol)}</span>
                ${superiorName ? `<span class="mgmt-item-detail">Superior: ${esc(superiorName)}</span>` : ''}
                ${m.discord_canal_id ? `<span class="mgmt-item-detail">Discord: ${m.discord_canal_id}</span>` : ''}
            </div>
            <div class="mgmt-item-actions">
                <button class="btn-sm btn-edit-miembro" data-id="${m.id}">Editar</button>
                <button class="btn-sm btn-danger-sm btn-delete-miembro" data-id="${m.id}">Eliminar</button>
            </div>
        </div>`;
    });

    html += `</div></div>`;
    $panel.innerHTML = html;

    // Create handler
    document.getElementById('btn-create-miembro').addEventListener('click', async () => {
        const form = document.getElementById('form-create-miembro');
        const body = {
            nombre: form.querySelector('[name="nombre"]').value.trim(),
            rol: form.querySelector('[name="rol"]').value.trim(),
            color: form.querySelector('[name="color"]').value,
            orden: parseInt(form.querySelector('[name="orden"]').value) || 0,
            superior_id: form.querySelector('[name="superior_id"]').value ? parseInt(form.querySelector('[name="superior_id"]').value) : null,
            discord_canal_id: form.querySelector('[name="discord_canal_id"]').value.trim() || null,
        };

        if (!body.nombre) { alert('El nombre es requerido'); return; }

        await fetch(`${API}/miembros`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        await loadConfig();
        renderEquipo();
    });

    // Delete handlers
    $panel.querySelectorAll('.btn-delete-miembro').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Eliminar este miembro?')) return;
            await fetch(`${API}/miembros/${btn.dataset.id}`, { method: 'DELETE' });
            await loadConfig();
            renderEquipo();
        });
    });

    // Edit handlers
    $panel.querySelectorAll('.btn-edit-miembro').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = parseInt(btn.dataset.id);
            const m = miembros.find(x => x.id === id);
            if (!m) return;
            openEditMiembroModal(m, miembros);
        });
    });
}

function openEditMiembroModal(miembro, allMiembros) {
    const $panel = document.getElementById('mgmt-panel');
    const existing = $panel.querySelector('.mgmt-edit-inline');
    if (existing) existing.remove();

    const $itemEl = $panel.querySelector(`.mgmt-item[data-id="${miembro.id}"]`);
    if (!$itemEl) return;

    let superiorOptions = '<option value="">Sin superior</option>';
    allMiembros.filter(m => m.id !== miembro.id).forEach(m => {
        const sel = m.id === miembro.superior_id ? ' selected' : '';
        superiorOptions += `<option value="${m.id}"${sel}>${esc(m.nombre)} (${esc(m.rol)})</option>`;
    });

    const $form = document.createElement('div');
    $form.className = 'mgmt-edit-inline';
    $form.innerHTML = `
        <div class="mgmt-form-row">
            <div class="mgmt-field mgmt-field-wide"><label>Nombre</label><input type="text" name="edit-nombre" value="${esc(miembro.nombre)}"></div>
            <div class="mgmt-field"><label>Rol</label><input type="text" name="edit-rol" value="${esc(miembro.rol)}"></div>
            <div class="mgmt-field"><label>Color</label><input type="color" name="edit-color" value="${miembro.color}"></div>
            <div class="mgmt-field"><label>Orden</label><input type="number" name="edit-orden" value="${miembro.orden}"></div>
            <div class="mgmt-field"><label>Superior</label><select name="edit-superior_id">${superiorOptions}</select></div>
            <div class="mgmt-field"><label>Discord Canal ID</label><input type="text" name="edit-discord_canal_id" value="${miembro.discord_canal_id || ''}"></div>
        </div>
        <div class="mgmt-edit-actions">
            <button class="btn-primary btn-sm" id="btn-save-miembro">Guardar</button>
            <button class="btn-sm" id="btn-cancel-miembro">Cancelar</button>
        </div>
    `;

    $itemEl.after($form);

    $form.querySelector('#btn-cancel-miembro').addEventListener('click', () => $form.remove());
    $form.querySelector('#btn-save-miembro').addEventListener('click', async () => {
        const body = {
            nombre: $form.querySelector('[name="edit-nombre"]').value.trim(),
            rol: $form.querySelector('[name="edit-rol"]').value.trim(),
            color: $form.querySelector('[name="edit-color"]').value,
            orden: parseInt($form.querySelector('[name="edit-orden"]').value) || 0,
            superior_id: $form.querySelector('[name="edit-superior_id"]').value ? parseInt($form.querySelector('[name="edit-superior_id"]').value) : null,
            discord_canal_id: $form.querySelector('[name="edit-discord_canal_id"]').value.trim() || null,
        };

        await fetch(`${API}/miembros/${miembro.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        await loadConfig();
        renderEquipo();
    });
}
