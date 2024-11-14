document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('saveReportForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            fetch(form.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/preview/report_sent';
                } else {
                    alert('Error saving report. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error saving report. Please try again.');
            });
        });
    }
});
