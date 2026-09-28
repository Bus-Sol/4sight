/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.flowNewsletterSubscribe = publicWidget.Widget.extend({
    selector: ".flow_newsletter_form",
    events: {
        "click .flow_newsletter_submit": "_onSubscribeClick",
    },

    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },

    async _onSubscribeClick(event) {
        event.preventDefault();

        if (this._isSubmitting) {
            return;
        }

        const input = this.el.querySelector(".flow_newsletter_email");
        const button = this.el.querySelector(".flow_newsletter_submit");
        const message = this.el.querySelector(".flow_newsletter_message");
        const email = input?.value.trim();

        if (!email) {
            input?.classList.add("is-invalid");
            this._setMessage(message, "Please enter your email address.", "danger");
            return;
        }

        input.classList.remove("is-invalid");
        this._setSubmitting(button, true);
        this._setMessage(message, "");

        try {
            const result = await this.rpc("/flow/newsletter/subscribe", { email });
            const isSuccess = Boolean(result?.success);
            this._setMessage(
                message,
                result?.message || "Unable to subscribe.",
                isSuccess ? "success" : "danger"
            );

            if (isSuccess) {
                input.value = "";
            } else {
                input.classList.add("is-invalid");
            }
        } catch (error) {
            console.error("Newsletter subscription failed:", error);
            input.classList.add("is-invalid");
            this._setMessage(message, "Something went wrong. Please try again.", "danger");
        } finally {
            this._setSubmitting(button, false);
        }
    },

    _setMessage(message, text, type) {
        if (message) {
            message.textContent = text;
            message.classList.remove("alert", "alert-success", "alert-danger", "py-2", "px-3", "mb-0");
            if (text) {
                message.classList.add("alert", `alert-${type}`, "py-2", "px-3", "mb-0");
                message.setAttribute("role", "status");
                message.setAttribute("aria-live", "polite");
            }
        }
    },

    _setSubmitting(button, isSubmitting) {
        this._isSubmitting = isSubmitting;
        if (button) {
            button.classList.toggle("disabled", isSubmitting);
            button.setAttribute("aria-disabled", String(isSubmitting));
        }
    },
});

export default publicWidget.registry.flowNewsletterSubscribe;
