// Add any interactive features here if needed
document.addEventListener('DOMContentLoaded', function() {
    // Auto-redirect after 5 seconds
    setTimeout(function() {
        const nextButton = document.querySelector('.btn-primary');
        if (nextButton) {
            nextButton.click();
        }
    }, 5000);
});
