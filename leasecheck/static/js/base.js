// Base JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Flash message handling
    const flashMessages = document.querySelectorAll('.flash-messages .alert');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 300);
            }, 5000);
        });
    }

    // Add CSRF token to all AJAX requests
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken) {
        document.addEventListener('ajax:beforeSend', function(e) {
            e.detail.xhr.setRequestHeader('X-CSRFToken', csrfToken);
        });
    }

    // Handle navigation menu on mobile
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
});
