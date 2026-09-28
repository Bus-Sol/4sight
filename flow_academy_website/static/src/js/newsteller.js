/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll(".s_newsletter_subscribe_form");

    for (const form of forms) {
        const input = form.querySelector(".js_subscribe_value");
        const button = form.querySelector(".js_subscribe_btn");
        const message = form.querySelector(".flow_newsletter_message");

        button.addEventListener("click", async () => {
            const email = input.value.trim();

            if (!email) {
                message.textContent = "Please enter your email address.";
                return;
            }

            button.disabled = true;
            message.textContent = "";

            try {
                const result = await rpc(
                    "/flow/newsletter/subscribe",
                    {
                        email: email,
                    }
                );

                if (result.success) {
                    message.textContent = result.message;
                    input.value = "";
                } else {
                    message.textContent =
                        result.message || "Unable to subscribe.";
                }
            } catch (error) {
                console.error("Newsletter subscription failed:", error);
                message.textContent =
                    "Something went wrong. Please try again.";
            } finally {
                button.disabled = false;
            }
        });
    }
});