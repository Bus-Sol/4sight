/** @odoo-module **/

import { registry } from "@web/core/registry";

const crmSalesGuardNotificationService = {
    dependencies: ["bus_service", "notification"],

    start(env, { bus_service, notification }) {
        bus_service.addEventListener("notification", ({ detail: notifications }) => {
            for (const item of notifications) {
                if (item.type !== "crm_sales_guard_notification") {
                    continue;
                }
                const payload = item.payload || {};
                const title = payload.title || "CRM Sales Communication";
                const message = payload.message || "New CRM communication";

                notification.add(message, {
                    title,
                    type: payload.type || "info",
                    sticky: false,
                });

                if ("Notification" in window && Notification.permission === "granted") {
                    const nativeNotification = new Notification(title, {
                        body: message,
                        tag: `crm-sales-guard-${payload.lead_id || "message"}`,
                        renotify: true,
                    });
                    nativeNotification.onclick = () => {
                        window.focus();
                        if (payload.action_url) {
                            window.location.href = payload.action_url;
                        }
                        nativeNotification.close();
                    };
                }
            }
        });
    },
};

registry.category("services").add(
    "crm_sales_guard_notification_service",
    crmSalesGuardNotificationService
);
