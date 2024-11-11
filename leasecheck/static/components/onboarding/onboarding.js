// Onboarding Component JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any interactive elements
    const choosePlanBtn = document.querySelector('.onboarding-choose-plan-btn');
    
    if (choosePlanBtn) {
        choosePlanBtn.addEventListener('click', function(e) {
            // Add analytics tracking
            console.log('Choose plan button clicked');
            
            // Add smooth scrolling animation
            e.preventDefault();
            const href = this.getAttribute('href');
            window.location.href = href;
        });
    }

    // Add intersection observer for animation triggers
    const animatedElements = document.querySelectorAll('.onboarding-feature-item');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(element);
    });
});
