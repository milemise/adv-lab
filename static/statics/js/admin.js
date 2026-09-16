function fetchPending() {
    fetch('/api/pending')
        .then(res => res.json())
        .then(items => {
            const container = document.getElementById('admin-pending-container');
            if (!container) return;
            
            container.innerHTML = '';
            if (items.length === 0) {
                container.innerHTML = '<p>No hay obras pendientes de revisión.</p>';
                return;
            }

            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'admin-item-card';
                div.innerHTML = `
                    <img src="${item.img}" width="120" style="object-fit:cover; border-radius:8px;">
                    <div>
                        <h4>${item.title}</h4>
                        <p><strong>Autor:</strong> ${item.firstname} ${item.lastname} (${item.instagram})</p>
                        <p>${item.desc}</p>
                        <button onclick="approveItem(${item.id})" class="btn-approve">Aprobar</button>
                        <button onclick="rejectItem(${item.id})" class="btn-reject">Rechazar</button>
                    </div>
                `;
                container.appendChild(div);
            });
        })
        .catch(err => console.error('Error cargando pendientes:', err));
}

function approveItem(id) {
    fetch('/api/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) fetchPending();
    });
}

function rejectItem(id) {
    fetch('/api/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) fetchPending();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('admin-pending-container')) {
        fetchPending();
    }
});