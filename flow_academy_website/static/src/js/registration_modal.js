/** @odoo-module **/


document.addEventListener('DOMContentLoaded', function() {
    // Cache modal element
    var modalElement = document.getElementById('modal_ticket_registration');
    if (!modalElement) return;

    var modal = new bootstrap.Modal(modalElement);
    var modalContent = modalElement.querySelector('.modal-content');

    // Add click handlers to all register buttons
    document.querySelectorAll('[data-bs-target="#modal_ticket_registration"]').forEach(button => {
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

                    // Re-initialize any Odoo-specific JS if needed
                    if (typeof odoo !== 'undefined') {
                        odoo.init();
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

    // Clear modal content when hidden to prevent stale data
    modalElement.addEventListener('hidden.bs.modal', function() {
        modalContent.innerHTML = '';
    });
});