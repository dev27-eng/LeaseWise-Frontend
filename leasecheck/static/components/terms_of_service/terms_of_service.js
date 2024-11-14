document.addEventListener('DOMContentLoaded', function() {
    class TermsOfService {
        constructor() {
            this.initializeElements();
            this.bindEvents();
        }

        initializeElements() {
            this.downloadBtn = document.getElementById('downloadPdf');
            this.sections = document.querySelectorAll('.terms-section');
            this.backButton = document.querySelector('.back-btn');
            this.lastViewed = null;
        }

        bindEvents() {
            if (this.downloadBtn) {
                this.downloadBtn.addEventListener('click', (e) => this.handleDownload(e));
            }

            if (this.backButton) {
                this.backButton.addEventListener('click', () => this.handleBackClick());
            }

            // Track section visibility for analytics
            this.setupIntersectionObserver();
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
                    const sectionTitle = entry.target.querySelector('h2')?.textContent;
                    if (sectionTitle && this.lastViewed !== sectionTitle) {
                        this.lastViewed = sectionTitle;
                        console.log(`Section viewed: ${sectionTitle}`);
                    }
                }
            });
        }

        async handleDownload(e) {
            e.preventDefault();
            
            try {
                // In preview mode, just show a success message
                alert('PDF download would be triggered here. In preview mode, this is just a demonstration.');
            } catch (error) {
                console.error('Error generating PDF:', error);
                alert('There was an error generating the PDF. Please try again later.');
            }
        }

        handleBackClick() {
            // Could be used for analytics before navigation
            console.log('User returned to legal information page');
        }
    }

    // Initialize the terms of service component
    new TermsOfService();
});
