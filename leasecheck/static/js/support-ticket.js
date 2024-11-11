class SupportTicket {
    constructor() {
        this.modal = document.getElementById('supportModal');
        this.form = document.getElementById('supportForm');
        this.closeBtn = this.modal.querySelector('.close-modal');
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.closeBtn.addEventListener('click', () => this.closeModal());
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    openModal(documentId) {
        document.getElementById('documentId').value = documentId;
        this.modal.style.display = 'block';
    }

    closeModal() {
        this.modal.style.display = 'none';
        this.form.reset();
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        try {
            const formData = new FormData(event.target);
            const response = await fetch('/submit-support-ticket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify(Object.fromEntries(formData))
            });
            
            if (response.ok) {
                alert('Support ticket submitted successfully. We will review your issue shortly.');
                this.closeModal();
            } else {
                throw new Error('Failed to submit support ticket');
            }
        } catch (error) {
            console.error('Error submitting support ticket:', error);
            alert('Failed to submit support ticket. Please try again.');
        }
    }
}
