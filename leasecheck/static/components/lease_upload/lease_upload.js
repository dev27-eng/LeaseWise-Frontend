document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('leaseFile');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    const uploadButton = document.getElementById('uploadButton');
    const form = document.getElementById('leaseUploadForm');

    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // File input change handler
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    // Remove file handler
    removeFile.addEventListener('click', () => {
        fileInput.value = '';
        fileInfo.style.display = 'none';
        uploadButton.disabled = true;
    });

    // Form submit handler
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/upload-lease', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                window.location.href = result.redirect;
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to upload file. Please try again.');
        }
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

            if (file.size > maxSize) {
                alert('File is too large. Maximum size is 10MB.');
                return;
            }

            if (!allowedTypes.includes(file.type)) {
                alert('Invalid file type. Please upload PDF, DOC, or DOCX files.');
                return;
            }

            fileName.textContent = file.name;
            fileInfo.style.display = 'flex';
            uploadButton.disabled = false;

            // If drag and dropped, set the file input
            if (fileInput.files.length === 0) {
                const dt = new DataTransfer();
                dt.items.add(file);
                fileInput.files = dt.files;
            }
        }
    }
});
