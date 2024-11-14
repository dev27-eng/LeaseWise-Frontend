document.addEventListener('DOMContentLoaded', function() {
    const supportForm = document.getElementById('supportForm');
    const issueType = document.getElementById('issueType');
    const priority = document.getElementById('priority');
    const description = document.getElementById('description');
    const contactMethod = document.getElementById('contactMethod');

    supportForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            issue_type: issueType.value,
            priority: priority.value,
            description: description.value,
            contact_method: contactMethod.value,
            document_id: document.querySelector('.document-id').textContent.split(': ')[1]
        };

        try {
            const response = await fetch('/submit-support-issue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                // Show success message
                const successMessage = document.createElement('div');
                successMessage.className = 'alert alert-success';
                successMessage.textContent = 'Support request submitted successfully. We will contact you shortly.';
                supportForm.insertBefore(successMessage, supportForm.firstChild);

                // Clear form
                supportForm.reset();

                // Redirect after 3 seconds
                setTimeout(() => {
                    window.location.href = data.redirect || '/';
                }, 3000);
            } else {
                throw new Error(data.message || 'Failed to submit support request');
            }
        } catch (error) {
            console.error('Error:', error);
            const errorMessage = document.createElement('div');
            errorMessage.className = 'alert alert-danger';
            errorMessage.textContent = 'Failed to submit support request. Please try again.';
            supportForm.insertBefore(errorMessage, supportForm.firstChild);
        }
    });

    // Dynamic form validation
    function validateForm() {
        const submitButton = supportForm.querySelector('button[type="submit"]');
        const isValid = issueType.value && priority.value && 
                       description.value.length >= 20 && contactMethod.value;
        submitButton.disabled = !isValid;
    }

    [issueType, priority, description, contactMethod].forEach(element => {
        element.addEventListener('input', validateForm);
    });

    // Initialize validation state
    validateForm();
});
