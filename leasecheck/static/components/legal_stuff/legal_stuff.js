document.addEventListener('DOMContentLoaded', function() {
    class LegalStuff {
        constructor() {
            this.initializeElements();
            this.bindEvents();
        }

        initializeElements() {
            this.form = document.getElementById('termsAcceptanceForm');
            this.acceptCheckbox = document.getElementById('acceptTerms');
            this.declineButton = document.getElementById('declineBtn');
            this.submitButton = this.form.querySelector('button[type="submit"]');
        }

        bindEvents() {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
            this.declineButton.addEventListener('click', () => this.handleDecline());
            this.acceptCheckbox.addEventListener('change', () => this.toggleSubmitButton());
        }

        toggleSubmitButton() {
            this.submitButton.disabled = !this.acceptCheckbox.checked;
        }

        async handleSubmit(e) {
            e.preventDefault();
            
            if (!this.acceptCheckbox.checked) {
                this.showError('Please accept the terms to continue');
                return;
            }

            try {
                const response = await fetch('/api/accept-terms', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                if (response.ok) {
                    window.location.href = '/checkout';
                } else {
                    const data = await response.json();
                    this.showError(data.error || 'Failed to process terms acceptance');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showError('An unexpected error occurred');
            }
        }

        handleDecline() {
            window.location.href = '/terms-declined';
        }

        showError(message) {
            // Implementation for error notification
            alert(message); // Replace with proper notification system
        }
    }

    // Initialize the legal stuff component
    new LegalStuff();
});
