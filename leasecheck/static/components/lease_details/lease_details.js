document.addEventListener('DOMContentLoaded', function() {
    window.confirmDetails = function() {
        const confirmed = confirm('Are you sure you want to confirm these lease details?');
        if (confirmed) {
            // Send confirmation to backend
            fetch('/confirm-lease-details', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    confirmed: true
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    alert('Error confirming details. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to confirm details. Please try again.');
            });
        }
    };
});
