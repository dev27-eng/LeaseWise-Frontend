class ProgressTracker {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.progressBar = this.container.querySelector('.progress-bar');
        this.progressText = this.container.querySelector('.progress-text');
        this.steps = Array.from(this.container.querySelectorAll('.step-item'));
    }

    updateProgress(status, progress) {
        // Update progress bar
        this.progressBar.style.width = `${progress}%`;
        if (this.progressText) {
            this.progressText.textContent = `${progress}% Complete`;
        }

        // Update steps based on status
        const steps = {
            'pending': 0,
            'validating': 25,
            'analyzing': 50,
            'processing': 75,
            'processed': 100,
            'error': null
        };

        // Reset all steps
        this.steps.forEach(step => {
            step.classList.remove('step-completed', 'step-current', 'step-error');
            step.classList.add('step-pending');
        });

        if (status === 'error') {
            this.steps[0].classList.add('step-error');
        } else {
            // Update steps based on progress
            if (progress >= 25) this.steps[0].classList.add('step-completed');
            if (progress >= 50) this.steps[1].classList.add('step-completed');
            if (progress >= 75) this.steps[2].classList.add('step-completed');
            if (progress === 100) this.steps[3].classList.add('step-completed');

            // Show current step
            if (progress < 25) this.steps[0].classList.add('step-current');
            else if (progress < 50) this.steps[1].classList.add('step-current');
            else if (progress < 75) this.steps[2].classList.add('step-current');
            else if (progress < 100) this.steps[3].classList.add('step-current');
        }
    }
}
