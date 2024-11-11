class UploadWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.uploadBox = this.container.querySelector('.upload-box');
        this.fileInput = this.container.querySelector('.file-input');
        this.fileList = this.container.querySelector('.file-list');
        this.errorMessage = this.container.querySelector('.error-message');
        this.successMessage = this.container.querySelector('.upload-success');
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.allowedTypes = {
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx'
        };

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.uploadBox.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadBox.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadBox.addEventListener('drop', (e) => this.handleDrop(e));
        this.fileInput.addEventListener('change', () => this.handleFileInputChange());
    }

    handleDragOver(e) {
        e.preventDefault();
        this.uploadBox.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadBox.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        this.uploadBox.classList.remove('drag-over');
        this.handleFiles(e.dataTransfer.files);
    }

    handleFileInputChange() {
        this.handleFiles(this.fileInput.files);
        this.fileInput.value = ''; // Reset input
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
        this.successMessage.style.display = 'none';
        setTimeout(() => {
            this.errorMessage.style.display = 'none';
        }, 5000);
    }

    showSuccess(message) {
        this.successMessage.textContent = message;
        this.successMessage.style.display = 'block';
        this.errorMessage.style.display = 'none';
        setTimeout(() => {
            this.successMessage.style.display = 'none';
        }, 5000);
    }

    validateFile(file) {
        if (!file) return false;

        if (file.size > this.maxFileSize) {
            this.showError('File size exceeds 10MB limit');
            return false;
        }

        if (!this.allowedTypes[file.type]) {
            this.showError('Invalid file type. Please upload PDF, DOC, or DOCX files only');
            return false;
        }

        return true;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    createFileItemElement(file) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${this.formatFileSize(file.size)}</div>
                <div class="upload-progress">
                    <div class="progress-bar"></div>
                </div>
            </div>
            <div class="file-remove">✕</div>
        `;

        fileItem.querySelector('.file-remove').addEventListener('click', () => {
            fileItem.remove();
        });

        return fileItem;
    }

    async uploadFile(file) {
        const fileItem = this.createFileItemElement(file);
        this.fileList.appendChild(fileItem);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload-lease', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                }
            });

            const progressBar = fileItem.querySelector('.progress-bar');
            progressBar.style.width = '100%';

            if (response.ok) {
                const data = await response.json();
                this.showSuccess('File uploaded successfully!');
                
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            } else {
                const error = await response.json();
                this.showError(error.error || 'Upload failed');
                fileItem.remove();
            }
        } catch (error) {
            this.showError('Network error occurred');
            fileItem.remove();
        }
    }

    handleFiles(files) {
        Array.from(files).forEach(file => {
            if (this.validateFile(file)) {
                this.uploadFile(file);
            }
        });
    }
}
