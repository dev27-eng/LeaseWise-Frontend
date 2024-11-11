document.addEventListener('DOMContentLoaded', function() {
    // Initialize risk report functionality
    class RiskReport {
        constructor() {
            this.initializeElements();
            this.bindEvents();
            this.loadRiskData();
        }

        initializeElements() {
            this.riskLevel = document.querySelector('.risk-level');
            this.findingsList = document.querySelector('.findings-list');
            this.recommendationsList = document.querySelector('.recommendations-list');
            this.saveButton = document.getElementById('save-report');
            this.contactButton = document.getElementById('contact-attorney');
        }

        bindEvents() {
            this.saveButton.addEventListener('click', () => this.handleSaveReport());
            this.contactButton.addEventListener('click', () => this.handleContactAttorney());
        }

        async loadRiskData() {
            try {
                const response = await fetch('/api/risk-report');
                const data = await response.json();
                this.updateRiskLevel(data.riskLevel);
                this.populateFindings(data.findings);
                this.populateRecommendations(data.recommendations);
            } catch (error) {
                console.error('Error loading risk data:', error);
                this.showError('Failed to load risk report data');
            }
        }

        updateRiskLevel(level) {
            this.riskLevel.setAttribute('data-level', level.toLowerCase());
            document.querySelector('.risk-text').textContent = `${level} Risk Level`;
        }

        populateFindings(findings) {
            this.findingsList.innerHTML = findings.map(finding => `
                <li class="finding-item">
                    <span class="icon ${finding.severity.toLowerCase()}"></span>
                    <div class="finding-content">
                        <h3>${finding.title}</h3>
                        <p>${finding.description}</p>
                    </div>
                </li>
            `).join('');
        }

        populateRecommendations(recommendations) {
            this.recommendationsList.innerHTML = recommendations.map(rec => `
                <div class="recommendation">
                    <h3>${rec.title}</h3>
                    <p>${rec.description}</p>
                </div>
            `).join('');
        }

        async handleSaveReport() {
            try {
                const response = await fetch('/api/save-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (response.ok) {
                    this.showSuccess('Report saved successfully');
                } else {
                    throw new Error('Failed to save report');
                }
            } catch (error) {
                console.error('Error saving report:', error);
                this.showError('Failed to save report');
            }
        }

        handleContactAttorney() {
            window.location.href = '/contact-attorney';
        }

        showSuccess(message) {
            // Implementation for success toast/notification
            alert(message); // Replace with proper notification system
        }

        showError(message) {
            // Implementation for error toast/notification
            alert(message); // Replace with proper notification system
        }
    }

    // Initialize the risk report
    new RiskReport();
});
