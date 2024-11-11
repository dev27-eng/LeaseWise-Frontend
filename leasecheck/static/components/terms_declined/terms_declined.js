document.addEventListener('DOMContentLoaded', function() {
    class TermsDeclined {
        constructor() {
            this.initializeElements();
            this.bindEvents();
        }

        initializeElements() {
            this.sections = document.querySelectorAll('.terms-declined-section');
            this.reviewButton = document.querySelector('.btn.primary');
            this.homeButton = document.querySelector('.btn.secondary');
        }

        bindEvents() {
            // Track section visibility for analytics
            this.setupIntersectionObserver();
            
            // Track button clicks
            if (this.reviewButton) {
                this.reviewButton.addEventListener('click', () => this.handleReviewClick());
            }
            
            if (this.homeButton) {
                this.homeButton.addEventListener('click', () => this.handleHomeClick());
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

        handleReviewClick() {
            // Could be used for analytics before navigation
            console.log('User chose to review terms again');
        }

        handleHomeClick() {
            // Could be used for analytics before navigation
            console.log('User returned to home page');
        }
    }

    // Initialize the terms declined component
    new TermsDeclined();
});
