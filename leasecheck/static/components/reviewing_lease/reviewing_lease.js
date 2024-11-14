document.addEventListener('DOMContentLoaded', function() {
    class LeaseReview {
        constructor() {
            this.initializeElements();
            this.bindEvents();
            this.startReview();
        }

        initializeElements() {
            this.progressBar = document.getElementById('progressBar');
            this.progressText = document.getElementById('progressText');
            this.statusList = document.getElementById('statusList');
            this.pageCount = document.getElementById('pageCount');
            this.timeRemaining = document.getElementById('timeRemaining');
            this.cancelButton = document.getElementById('cancelReview');
            this.currentProgress = 0;
            this.statuses = ['document', 'clauses', 'compliance', 'risks', 'report'];
            this.currentStatusIndex = 0;
        }

        bindEvents() {
            this.cancelButton.addEventListener('click', () => this.handleCancel());
        }

        async startReview() {
            try {
                await this.initializeReview();
                this.startProgressSimulation();
            } catch (error) {
                console.error('Error starting review:', error);
                this.handleError('Failed to start review process');
            }
        }

        async initializeReview() {
            try {
                const response = await fetch('/api/review/initialize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Failed to initialize review');
                }

                const data = await response.json();
                this.updateDocumentInfo(data);
            } catch (error) {
                console.error('Error initializing review:', error);
                throw error;
            }
        }

        updateDocumentInfo(data) {
            if (data.pageCount) {
                this.pageCount.textContent = `${data.pageCount} pages`;
            }
            this.updateEstimatedTime(data.pageCount || 1);
        }

        updateEstimatedTime(pageCount) {
            const baseTime = 30; // Base time in seconds
            const estimatedSeconds = baseTime + (pageCount * 5);
            this.totalTime = estimatedSeconds;
            this.updateTimeRemaining(estimatedSeconds);
        }

        updateTimeRemaining(seconds) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            this.timeRemaining.textContent = 
                `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        }

        startProgressSimulation() {
            const intervalTime = (this.totalTime * 1000) / 100; // Divide total time into 100 steps
            
            this.progressInterval = setInterval(() => {
                if (this.currentProgress >= 100) {
                    clearInterval(this.progressInterval);
                    this.completeReview();
                    return;
                }

                this.currentProgress += 1;
                this.updateProgress(this.currentProgress);
                
                // Update status at certain thresholds
                if (this.currentProgress % 20 === 0) {
                    this.updateStatus();
                }

                const remainingSeconds = Math.ceil((100 - this.currentProgress) * this.totalTime / 100);
                this.updateTimeRemaining(remainingSeconds);
            }, intervalTime);
        }

        updateProgress(progress) {
            this.progressBar.style.width = `${progress}%`;
            this.progressText.textContent = `${progress}%`;
        }

        updateStatus() {
            if (this.currentStatusIndex < this.statuses.length) {
                const currentStatus = this.statuses[this.currentStatusIndex];
                const statusItem = this.statusList.querySelector(`[data-status="${currentStatus}"]`);
                
                if (statusItem) {
                    statusItem.classList.remove('pending');
                    statusItem.classList.add('completed');
                }

                if (this.currentStatusIndex + 1 < this.statuses.length) {
                    const nextStatus = this.statuses[this.currentStatusIndex + 1];
                    const nextItem = this.statusList.querySelector(`[data-status="${nextStatus}"]`);
                    if (nextItem) {
                        nextItem.classList.add('pending');
                    }
                }

                this.currentStatusIndex++;
            }
        }

        async completeReview() {
            try {
                const response = await fetch('/api/review/complete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    window.location.href = '/risk-report';
                } else {
                    throw new Error('Failed to complete review');
                }
            } catch (error) {
                console.error('Error completing review:', error);
                this.handleError('Failed to complete review process');
            }
        }

        async handleCancel() {
            if (confirm('Are you sure you want to cancel the review? All progress will be lost.')) {
                try {
                    await fetch('/api/review/cancel', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    window.location.href = '/lease-upload';
                } catch (error) {
                    console.error('Error canceling review:', error);
                    this.handleError('Failed to cancel review');
                }
            }
        }

        handleError(message) {
            // Implementation for error toast/notification
            alert(message); // Replace with proper notification system
        }
    }

    // Initialize the lease review
    new LeaseReview();
});
