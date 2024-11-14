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
            this.toggleSubmitButton();
        }

        bindEvents() {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
            this.declineButton.addEventListener('click', () => this.handleDecline());
            this.acceptCheckbox.addEventListener('change', () => this.toggleSubmitButton());
        }

        toggleSubmitButton() {
            if (this.submitButton) {
                this.submitButton.disabled = !this.acceptCheckbox.checked;
                this.submitButton.classList.toggle('disabled', !this.acceptCheckbox.checked);
            }
        }

        async handleSubmit(e) {
            e.preventDefault();
            
            if (!this.acceptCheckbox.checked) {
                this.showError('Please accept the terms to continue');
                return;
            }

            try {
                // In preview mode, just redirect to the next step
                window.location.href = '/preview/checkout';
            } catch (error) {
                console.error('Error:', error);
                this.showError('An unexpected error occurred');
            }
        }

        handleDecline() {
            window.location.href = '/preview/terms_declined';
        }

        showError(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            
            // Remove any existing error messages
            const existingError = this.form.querySelector('.error-message');
            if (existingError) {
                existingError.remove();
            }
            
            // Insert error message after the checkbox group
            const checkboxGroup = this.form.querySelector('.checkbox-group');
            checkboxGroup.insertAdjacentElement('afterend', errorDiv);
            
            // Remove error message after 5 seconds
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        }
    }

    // Initialize the legal stuff component
    new LegalStuff();
});
