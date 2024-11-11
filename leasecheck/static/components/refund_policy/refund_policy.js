document.addEventListener('DOMContentLoaded', function() {
    class RefundPolicy {
        constructor() {
            this.initializeElements();
            this.bindEvents();
        }

        initializeElements() {
            this.sections = document.querySelectorAll('.refund-section');
            this.backButton = document.querySelector('.btn.primary');
        }

        bindEvents() {
            // Track section visibility for analytics
            this.setupIntersectionObserver();
            
            // Track back button clicks
            if (this.backButton) {
                this.backButton.addEventListener('click', () => this.handleBackClick());
            }
        }

        setupIntersectionObserver() {
            const observer = new IntersectionObserver(
                (entries) => this.handleSectionVisibility(entries),
                { threshold: 0.5 }
            );

            this.sections.forEach(section => observer.observe(section));
        }

        handleSectionVisibility(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Could be used for analytics or progress tracking
                    console.log(`Section viewed: ${entry.target.querySelector('h2').textContent}`);
                }
            });
        }

        handleBackClick() {
            // Could be used for analytics before navigation
            console.log('User returned to legal information page');
        }
    }

    // Initialize the refund policy component
    new RefundPolicy();
});
