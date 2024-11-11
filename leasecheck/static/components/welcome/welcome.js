// Welcome Component JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Add any welcome screen specific functionality here
    console.log('Welcome component loaded');
    
    // Example: Add smooth scroll for navigation links
    const startButton = document.querySelector('.welcome-start-btn');
    if (startButton) {
        startButton.addEventListener('click', function(e) {
            // Add any click animations or tracking here
            console.log('Start review button clicked');
        });
    }
});
