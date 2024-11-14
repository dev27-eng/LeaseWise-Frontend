document.addEventListener('DOMContentLoaded', function() {
    window.toggleResolved = function(errorId) {
        fetch(`/toggle-error-resolved/${errorId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const errorItem = document.querySelector(`[data-error-id="${errorId}"]`);
                errorItem.classList.toggle('resolved');
                updateErrorCount();
            }
        })
        .catch(error => console.error('Error:', error));
    };

    window.showDetails = function(errorId) {
        fetch(`/error-details/${errorId}`)
        .then(response => response.json())
        .then(data => {
            // Create and show modal with error details
            const modal = document.createElement('div');
            modal.className = 'error-modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <h3>${data.title}</h3>
                    <p>${data.description}</p>
                    <div class="modal-actions">
                        <button onclick="closeModal()">Close</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        })
        .catch(error => console.error('Error:', error));
    };

    window.downloadReport = function() {
        window.location.href = '/download-error-report';
    };

    window.proceedToSupport = function() {
        window.location.href = '/support-issue';
    };

    function updateErrorCount() {
        const unresolvedErrors = document.querySelectorAll('.error-item:not(.resolved)').length;
        const errorStatus = document.querySelector('.error-status');
        errorStatus.textContent = `${unresolvedErrors} Issues Found`;
    }
});
