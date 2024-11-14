document.addEventListener('DOMContentLoaded', function() {
    // Auto-redirect after 10 seconds
    setTimeout(function() {
        const nextButton = document.querySelector('.btn-primary');
        if (nextButton) {
            nextButton.click();
        }
    }, 10000);

    // Add countdown timer
    let timeLeft = 10;
    const timer = setInterval(function() {
        timeLeft--;
        if (timeLeft <= 0) {
            clearInterval(timer);
        }
    }, 1000);
});
