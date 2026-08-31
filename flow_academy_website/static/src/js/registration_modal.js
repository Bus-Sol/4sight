/** @odoo-module **/


document.addEventListener('DOMContentLoaded', function() {
    // Cache modal element
    var modalElement = document.getElementById('modal_ticket_registration');
    if (!modalElement) return;

    var modalContent = modalElement.querySelector('.modal-content');
    var modal = bootstrap.Modal.getOrCreateInstance(modalElement);

    // Add click handlers to all register buttons
    document.querySelectorAll('.register-btn').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();

            var eventId = this.getAttribute('data-event-id');

            // Show loading state
            modalContent.innerHTML = `
                <div class="modal-body text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3">Loading registration form...</p>
                </div>
            `;

            // Show modal immediately with loading state
            modal.show();

            // Fetch modal content for this specific event
            fetch('/event/get_registration_form/' + eventId)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    // Update modal content
                    modalContent.innerHTML = html;

                    // Re-initialize any Bootstrap components in the new content
                    var forms = modalContent.querySelectorAll('form');
                    forms.forEach(form => {
                        // Re-initialize form validation if needed
                    });

                    // Re-attach event listeners for buttons inside modal
                    var closeBtn = modalContent.querySelector('[data-bs-dismiss="modal"]');
                    if (closeBtn) {
                        closeBtn.addEventListener('click', function() {
                            modal.hide();
                        });
                    }
                })
                .catch(error => {
                    console.error('Error loading registration form:', error);
                    modalContent.innerHTML = `
                        <div class="modal-body text-center py-5">
                            <div class="alert alert-danger">
                                <p>Error loading registration form. Please try again.</p>
                                <button class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    `;
                });
        });
    });
});