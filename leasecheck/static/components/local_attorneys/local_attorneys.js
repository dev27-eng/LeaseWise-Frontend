document.addEventListener('DOMContentLoaded', function() {
    const mockAttorneys = [
        {
            name: "Sarah Johnson",
            specialty: "Real Estate Law",
            experience: "15 years",
            rating: 4.8,
            cases: 250,
            success: "95%"
        },
        {
            name: "Michael Chen",
            specialty: "Property Law",
            experience: "12 years",
            rating: 4.9,
            cases: 180,
            success: "92%"
        },
        {
            name: "Emily Rodriguez",
            specialty: "Housing Law",
            experience: "8 years",
            rating: 4.7,
            cases: 120,
            success: "90%"
        }
    ];

    function searchAttorneys() {
        const location = document.getElementById('locationInput').value;
        const grid = document.getElementById('attorneysGrid');
        const noResults = document.getElementById('noResults');

        // Clear existing results
        grid.innerHTML = '';

        if (location.trim() === '') {
            noResults.style.display = 'block';
            return;
        }

        // For demo purposes, always show mock attorneys
        mockAttorneys.forEach(attorney => {
            const card = createAttorneyCard(attorney);
            grid.appendChild(card);
        });

        noResults.style.display = mockAttorneys.length === 0 ? 'block' : 'none';
    }

    function createAttorneyCard(attorney) {
        const card = document.createElement('div');
        card.className = 'attorney-card';
        
        card.innerHTML = `
            <div class="attorney-photo">👤</div>
            <h3 class="attorney-name">${attorney.name}</h3>
            <div class="attorney-specialty">${attorney.specialty}</div>
            <div class="attorney-stats">
                <div class="stat-item">
                    <div class="stat-label">Experience</div>
                    <div class="stat-value">${attorney.experience}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Rating</div>
                    <div class="stat-value">${attorney.rating}/5</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Cases</div>
                    <div class="stat-value">${attorney.cases}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Success Rate</div>
                    <div class="stat-value">${attorney.success}</div>
                </div>
            </div>
            <button class="contact-btn" onclick="contactAttorney('${attorney.name}')">Contact Attorney</button>
        `;
        
        return card;
    }

    function contactAttorney(attorneyName) {
        // Store attorney name in session storage for the acknowledgment page
        sessionStorage.setItem('selectedAttorney', attorneyName);
        window.location.href = "/preview/lawyer_message_acknowledgment";
    }

    // Initialize search on page load
    searchAttorneys();

    // Add event listener to search button
    const searchButton = document.querySelector('.search-btn');
    if (searchButton) {
        searchButton.addEventListener('click', searchAttorneys);
    }

    // Add event listener for Enter key on search input
    const searchInput = document.getElementById('locationInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchAttorneys();
            }
        });
    }
});
