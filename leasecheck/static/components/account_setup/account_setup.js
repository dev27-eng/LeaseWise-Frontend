document.addEventListener('DOMContentLoaded', function() {
    class AccountSetup {
        constructor() {
            this.initializeElements();
            this.bindEvents();
        }

        initializeElements() {
            this.emailForm = document.getElementById('email-form');
            this.verificationForm = document.getElementById('verification-form');
            this.emailSection = document.querySelector('.email-section');
            this.verificationSection = document.querySelector('.verification-section');
            this.finalSection = document.querySelector('.final-section');
            this.codeInputs = document.querySelectorAll('.code-input');
            this.resendCodeBtn = document.getElementById('resend-code');
            this.emailInput = document.querySelector('input[type="email"]');
            this.emailError = document.getElementById('email-error');
            this.verificationError = document.getElementById('verification-error');
        }

        bindEvents() {
            this.emailForm.addEventListener('submit', (e) => this.handleEmailSubmit(e));
            this.verificationForm.addEventListener('submit', (e) => this.handleVerificationSubmit(e));
            this.resendCodeBtn.addEventListener('click', (e) => this.handleResendCode(e));
            this.setupCodeInputs();
        }

        setupCodeInputs() {
            this.codeInputs.forEach((input, index) => {
                input.addEventListener('input', (e) => {
                    if (e.target.value.length === 1) {
                        if (index < this.codeInputs.length - 1) {
                            this.codeInputs[index + 1].focus();
                        }
                    }
                });

                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Backspace' && !e.target.value) {
                        if (index > 0) {
                            this.codeInputs[index - 1].focus();
                        }
                    }
                });
            });
        }

        async handleEmailSubmit(e) {
            e.preventDefault();
            const email = this.emailInput.value;
            
            if (!this.validateEmail(email)) {
                this.showError(this.emailError, 'Please enter a valid email address');
                return;
            }

            try {
                const response = await fetch('/api/send-verification-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email })
                });

                if (response.ok) {
                    this.emailSection.style.display = 'none';
                    this.verificationSection.style.display = 'block';
                } else {
                    const data = await response.json();
                    this.showError(this.emailError, data.error || 'Failed to send verification code');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showError(this.emailError, 'An unexpected error occurred');
            }
        }

        async handleVerificationSubmit(e) {
            e.preventDefault();
            const code = Array.from(this.codeInputs).map(input => input.value).join('');
            
            if (code.length !== 6) {
                this.showError(this.verificationError, 'Please enter a valid verification code');
                return;
            }

            try {
                const response = await fetch('/api/verify-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ code })
                });

                if (response.ok) {
                    this.verificationSection.style.display = 'none';
                    this.finalSection.style.display = 'block';
                } else {
                    const data = await response.json();
                    this.showError(this.verificationError, data.error || 'Invalid verification code');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showError(this.verificationError, 'An unexpected error occurred');
            }
        }

        async handleResendCode(e) {
            e.preventDefault();
            const email = this.emailInput.value;

            try {
                const response = await fetch('/api/send-verification-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email })
                });

                if (!response.ok) {
                    const data = await response.json();
                    this.showError(this.verificationError, data.error || 'Failed to resend code');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showError(this.verificationError, 'Failed to resend verification code');
            }
        }

        validateEmail(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        }

        showError(element, message) {
            element.textContent = message;
            element.style.display = 'block';
        }
    }

    // Initialize the account setup component
    new AccountSetup();
});
