document.addEventListener('DOMContentLoaded', function() {
    class CheckoutComponent {
        constructor() {
            this.form = document.getElementById('payment-form');
            this.errorDiv = document.getElementById('card-errors');
            this.submitButton = this.form.querySelector('button[type="submit"]');
            
            this.bindEvents();
        }

        bindEvents() {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        async handleSubmit(e) {
            e.preventDefault();
            
            // Disable submit button to prevent double submission
            this.submitButton.disabled = true;
            
            try {
                // Here we would normally integrate with Stripe or another payment processor
                // For now, we'll just simulate a successful payment
                await this.simulatePayment();
                
                // Redirect to payment success page
                window.location.href = '/payment-status?status=success';
            } catch (error) {
                this.showError(error.message);
                this.submitButton.disabled = false;
            }
        }

        async simulatePayment() {
            // Simulate payment processing
            return new Promise((resolve, reject) => {
                setTimeout(() => {
                    // For demo purposes, always succeed
                    resolve();
                }, 1500);
            });
        }

        showError(message) {
            this.errorDiv.textContent = message;
            this.errorDiv.style.display = 'block';
        }

        clearError() {
            this.errorDiv.textContent = '';
            this.errorDiv.style.display = 'none';
        }
    }

    // Initialize the checkout component
    new CheckoutComponent();
});
