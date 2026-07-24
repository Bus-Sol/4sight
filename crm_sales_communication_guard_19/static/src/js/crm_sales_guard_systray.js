/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class CrmSalesGuardSystray extends Component {
    static template = "crm_sales_communication_guard_19.CrmSalesGuardSystray";
    static props = {};

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            supported: "Notification" in window,
            permission: "Notification" in window ? Notification.permission : "unsupported",
        });
    }

    async onEnableBrowserNotifications() {
        if (!this.state.supported) {
            this.notification.add(_t("This browser does not support native notifications."), {
                title: _t("CRM Sales Guard"),
                type: "warning",
            });
            return;
        }
        this.state.permission = await Notification.requestPermission();
        this.notification.add(
            this.state.permission === "granted"
                ? _t("Native browser notifications are enabled.")
                : _t("Browser notification permission was not granted."),
            {
                title: _t("CRM Sales Guard"),
                type: this.state.permission === "granted" ? "success" : "warning",
            }
        );
    }
}

registry.category("systray").add(
    "CrmSalesGuardSystray",
    { Component: CrmSalesGuardSystray },
    { sequence: 45 }
);
