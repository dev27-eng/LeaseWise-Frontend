document.addEventListener('DOMContentLoaded', function() {
    class AccountSetup {
        constructor() {
            this.initializeElements();
            this.bindEvents();
        }

        initializeElements() {
            this.form = document.getElementById('accountSetupForm');
            this.sendCodeBtn = document.getElementById('sendCodeBtn');
            this.verifyCodeBtn = document.getElementById('verifyCodeBtn');
            this.emailInput = document.getElementById('email');
            this.verificationCodeInput = document.getElementById('verificationCode');
        }

        bindEvents() {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
            this.sendCodeBtn.addEventListener('click', () => this.handleSendCode());
            this.verifyCodeBtn.addEventListener('click', () => this.handleVerifyCode());
            this.emailInput.addEventListener('input', () => this.validateEmail());
        }

        async handleSubmit(e) {
            e.preventDefault();
            if (!this.validateForm()) {
                return;
            }

            try {
                const formData = new FormData(this.form);
                const response = await fetch('/api/account-setup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(Object.fromEntries(formData))
                });

                if (response.ok) {
                    window.location.href = '/legal-stuff';
                } else {
                    const data = await response.json();
                    this.showError(data.error || 'Failed to create account');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showError('An unexpected error occurred');
            }
        }

        async handleSendCode() {
            if (!this.validateEmail()) {
                return;
            }

            try {
                const response = await fetch('/api/send-verification-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email: this.emailInput.value })
                });

                if (response.ok) {
                    this.showSuccess('Verification code sent');
                    this.sendCodeBtn.disabled = true;
                    setTimeout(() => {
                        this.sendCodeBtn.disabled = false;
                    }, 60000); // Enable after 1 minute
                } else {
                    const data = await response.json();
                    this.showError(data.error || 'Failed to send code');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showError('Failed to send verification code');
            }
        }

        async handleVerifyCode() {
            const code = this.verificationCodeInput.value.trim();
            if (!code) {
                this.showError('Please enter verification code');
                return;
            }

            try {
                const response = await fetch('/api/verify-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ code })
                });

                if (response.ok) {
                    this.showSuccess('Email verified successfully');
                    this.verificationCodeInput.disabled = true;
                    this.verifyCodeBtn.disabled = true;
                } else {
                    const data = await response.json();
                    this.showError(data.error || 'Invalid verification code');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showError('Failed to verify code');
            }
        }

        validateEmail() {
            const email = this.emailInput.value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            const isValid = emailRegex.test(email);
            
            if (!isValid) {
                this.showError('Please enter a valid email address');
            }
            
            return isValid;
        }

        validateForm() {
            const requiredFields = this.form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    this.showError(`${field.name} is required`);
                    isValid = false;
                }
            });

            return isValid && this.validateEmail();
        }

        showSuccess(message) {
            // Implementation for success notification
            alert(message); // Replace with proper notification system
        }

        showError(message) {
            // Implementation for error notification
            alert(message); // Replace with proper notification system
        }
    }

    // Initialize the account setup
    new AccountSetup();
});
