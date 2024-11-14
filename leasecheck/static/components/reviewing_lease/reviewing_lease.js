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
            
            // Mock data for preview
            this.mockData = {
                pageCount: 12,
                totalTime: 90 // 90 seconds for preview
            };
        }

        bindEvents() {
            this.cancelButton.addEventListener('click', () => this.handleCancel());
        }

        startReview() {
            this.initializeReview();
            this.startProgressSimulation();
        }

        initializeReview() {
            this.updateDocumentInfo();
        }

        updateDocumentInfo() {
            this.pageCount.textContent = `${this.mockData.pageCount} pages`;
            this.updateEstimatedTime(this.mockData.pageCount);
        }

        updateEstimatedTime(pageCount) {
            this.totalTime = this.mockData.totalTime;
            this.updateTimeRemaining(this.totalTime);
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

        completeReview() {
            // For preview, just redirect to risk report
            window.location.href = '/risk-report';
        }

        handleCancel() {
            if (confirm('Are you sure you want to cancel the review? All progress will be lost.')) {
                window.location.href = '/lease-upload';
            }
        }
    }

    // Initialize the lease review
    new LeaseReview();
});