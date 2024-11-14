document.addEventListener('DOMContentLoaded', function() {
    class RefundPolicy {
        constructor() {
            this.initializeElements();
            this.bindEvents();
            this.lastViewed = null;
        }

        initializeElements() {
            this.sections = document.querySelectorAll('.policy-section');
            this.backButton = document.querySelector('.back-btn');
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
                    const sectionTitle = entry.target.querySelector('h3')?.textContent;
                    if (sectionTitle && this.lastViewed !== sectionTitle) {
                        this.lastViewed = sectionTitle;
                        console.log(`Section viewed: ${sectionTitle}`);
                    }
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
