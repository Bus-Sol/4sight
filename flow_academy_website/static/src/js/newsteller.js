/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.flowNewsletterSubscribe = publicWidget.Widget.extend({
    selector: ".flow_newsletter_subscribe_form",
    events: {
        "click .js_subscribe_btn": "_onSubscribeClick",
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

        const input = this.el.querySelector(".js_subscribe_value");
        const button = this.el.querySelector(".js_subscribe_btn");
        const message = this.el.querySelector(".flow_newsletter_message");
        const email = input?.value.trim();

        if (!email) {
            this._setMessage(message, "Please enter your email address.");
            return;
        }

        this._setSubmitting(button, true);
        this._setMessage(message, "");

        try {
            const result = await this.rpc("/flow/newsletter/subscribe", { email });
            this._setMessage(message, result?.message || "Unable to subscribe.");

            if (result?.success) {
                input.value = "";
            }
        } catch (error) {
            console.error("Newsletter subscription failed:", error);
            this._setMessage(message, "Something went wrong. Please try again.");
        } finally {
            this._setSubmitting(button, false);
        }
    },

    _setMessage(message, text) {
        if (message) {
            message.textContent = text;
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
