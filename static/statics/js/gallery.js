function fetchGallery() {
    fetch('/api/gallery')
        .then(res => res.json())
        .then(items => {
            const galleryContainer = document.getElementById('gallery-container');
            if (!galleryContainer) return;

            galleryContainer.innerHTML = '';
            if (items.length === 0) {
                galleryContainer.innerHTML = '<p>No hay obras publicadas todavía.</p>';
                return;
            }

            items.forEach(item => {
                const card = document.createElement('div');
                card.className = 'gallery-card';
                card.innerHTML = `
                    <img src="${item.img}" alt="${item.title}">
                    <h3>${item.title}</h3>
                    <p>Artista: ${item.firstname} ${item.lastname}</p>
                    ${item.instagram ? `<a href="https://instagram.com/${item.instagram.replace('@','')}" target="_blank">@${item.instagram.replace('@','')}</a>` : ''}
                    <p>${item.desc}</p>
                `;
                galleryContainer.appendChild(card);
            });
        })
        .catch(err => console.error('Error cargando galería:', err));
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('gallery-container')) {
        fetchGallery();
    }
});