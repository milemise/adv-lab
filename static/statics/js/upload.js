function handleUpload(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData();

    const instagramInput = document.getElementById('up-instagram');
    const firstName = document.getElementById('up-firstname');
    const lastName = document.getElementById('up-lastname');
    const title = document.getElementById('up-title');
    const desc = document.getElementById('up-desc');
    const imageInput = document.getElementById('up-image'); // Asegúrate que tu input de tipo file tenga id="up-image"
    const successMsg = document.getElementById('upload-success-msg');

    formData.append('firstname', firstName ? firstName.value.trim() : '');
    formData.append('lastname', lastName ? lastName.value.trim() : '');
    formData.append('instagram', instagramInput ? instagramInput.value.trim() : '');
    formData.append('title', title ? title.value.trim().toUpperCase() : '');
    formData.append('desc', desc ? desc.value.trim() : '');
    
    if (imageInput && imageInput.files[0]) {
        formData.append('image', imageInput.files[0]);
    }

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (successMsg) successMsg.classList.remove('hidden');
            setTimeout(() => {
                if (typeof closeUploadModal === 'function') closeUploadModal();
                form.reset();
                if (successMsg) successMsg.classList.add('hidden');
                const preview = document.getElementById('upload-preview');
                if (preview) preview.classList.add('hidden');
                const placeholder = document.getElementById('upload-placeholder');
                if (placeholder) placeholder.classList.remove('hidden');
            }, 1800);
        } else {
            alert('Error al subir la obra');
        }
    })
    .catch(err => {
        console.error(err);
        alert('Error de conexión con el servidor');
    });
}