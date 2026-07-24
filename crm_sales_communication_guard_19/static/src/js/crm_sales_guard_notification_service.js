/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

const crmSalesGuardNotificationService = {
    dependencies: ["bus_service", "notification", "action"],

    start(env, { bus_service, notification, action }) {
        const handler = ({ detail: notifications }) => {
            for (const item of notifications || []) {
                if (item.type !== "crm_sales_guard_notification") {
                    continue;
                }
                const payload = item.payload || {};
                const title = payload.title || _t("CRM Sales Communication");
                const message = payload.message || _t("New CRM communication");

                notification.add(message, {
                    title,
                    type: payload.type || "info",
                    sticky: false,
                });

                if ("Notification" in window && Notification.permission === "granted") {
                    const nativeNotification = new Notification(title, {
                        body: message,
                        tag: `crm-sales-guard-${payload.lead_id || "message"}`,
                    });
                    nativeNotification.onclick = () => {
                        window.focus();
                        if (payload.lead_id) {
                            action.doAction({
                                type: "ir.actions.act_window",
                                res_model: "crm.lead",
                                res_id: payload.lead_id,
                                views: [[false, "form"]],
                                target: "current",
                            });
                        }
                        nativeNotification.close();
                    };
                }
            }
        };
        bus_service.addEventListener("notification", handler);
        return () => bus_service.removeEventListener("notification", handler);
    },
};

registry.category("services").add(
    "crm_sales_guard_notification_service",
    crmSalesGuardNotificationService
);
