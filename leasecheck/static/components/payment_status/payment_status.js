document.addEventListener('DOMContentLoaded', function() {
    class PaymentStatus {
        constructor() {
            this.initializeElements();
            this.bindEvents();
        }

        initializeElements() {
            this.container = document.querySelector('.payment-status-container');
            this.actionButtons = document.querySelectorAll('.action-btn');
        }

        bindEvents() {
            this.actionButtons.forEach(button => {
                button.addEventListener('click', (e) => this.handleButtonClick(e));
            });
        }

        handleButtonClick(e) {
            // Add click animation
            const button = e.currentTarget;
            button.style.transform = 'scale(0.98)';
            setTimeout(() => {
                button.style.transform = 'scale(1)';
            }, 100);
        }
    }

    // Initialize the payment status component
    new PaymentStatus();
});
