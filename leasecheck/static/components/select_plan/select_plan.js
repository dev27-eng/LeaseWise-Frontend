document.addEventListener('DOMContentLoaded', function() {
    class PlanSelector {
        constructor() {
            this.initializeElements();
            this.bindEvents();
        }

        initializeElements() {
            this.planCards = document.querySelectorAll('.plan-card');
            this.selectButtons = document.querySelectorAll('.select-plan-btn');
        }

        bindEvents() {
            // Add hover effects for plan cards
            this.planCards.forEach(card => {
                card.addEventListener('mouseenter', () => this.handleCardHover(card, true));
                card.addEventListener('mouseleave', () => this.handleCardHover(card, false));
            });

            // Add click tracking for plan selection
            this.selectButtons.forEach(button => {
                button.addEventListener('click', (e) => this.handlePlanSelection(e));
            });

            // Add keyboard navigation
            this.planCards.forEach(card => {
                card.addEventListener('keydown', (e) => this.handleKeyboardNavigation(e, card));
            });
        }

        handleCardHover(card, isHovering) {
            if (isHovering) {
                card.style.transform = 'translateY(-5px)';
                card.style.boxShadow = '0 8px 12px rgba(0, 0, 0, 0.1)';
            } else {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
            }
        }

        handlePlanSelection(e) {
            const planCard = e.target.closest('.plan-card');
            const planId = planCard.dataset.plan;
            
            // Track plan selection (can be extended with analytics)
            console.log(`Selected plan: ${planId}`);
            
            // Optional: Add loading state
            const button = e.target;
            button.style.opacity = '0.7';
            button.textContent = 'Processing...';
            
            // The actual navigation is handled by the href attribute
        }

        handleKeyboardNavigation(e, card) {
            const button = card.querySelector('.select-plan-btn');
            
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                button.click();
            }
        }
    }

    // Initialize the plan selector
    new PlanSelector();
});
