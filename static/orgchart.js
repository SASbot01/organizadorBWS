// ── Organigrama View ─────────────────────────────────────

async function renderOrganigramaView() {
    const $panel = document.getElementById('mgmt-panel');
    $panel.innerHTML = '<div class="mgmt-section"><div class="loading">Cargando organigrama...</div></div>';

    const res = await fetch(`${API}/miembros/orgchart`);
    const data = await res.json();
    const tree = data.orgchart || [];

    if (tree.length === 0) {
        $panel.innerHTML = '<div class="mgmt-section"><p class="empty-msg">No hay miembros registrados. Agrega miembros en la pestana "Equipo".</p></div>';
        return;
    }

    let html = '<div class="mgmt-section"><div class="orgchart-container">';
    html += renderOrgNode(tree);
    html += '</div></div>';

    $panel.innerHTML = html;
}

function renderOrgNode(nodes) {
    if (!nodes || nodes.length === 0) return '';

    let html = '<ul class="org-tree">';
    nodes.forEach(node => {
        const hasChildren = node.hijos && node.hijos.length > 0;
        html += `<li>
            <div class="org-node" style="border-color:${node.color}">
                <div class="org-node-avatar" style="background:${node.color}">
                    ${node.nombre.charAt(0).toUpperCase()}
                </div>
                <div class="org-node-info">
                    <span class="org-node-name">${esc(node.nombre)}</span>
                    <span class="org-node-role" style="color:${node.color}">${esc(node.rol)}</span>
                </div>
            </div>
            ${hasChildren ? renderOrgNode(node.hijos) : ''}
        </li>`;
    });
    html += '</ul>';
    return html;
}
