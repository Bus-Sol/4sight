/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CrmSalesGuardSystray extends Component {
    static template = "crm_incoming_email_badge_17.CrmSalesGuardSystray";

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            supported: "Notification" in window,
            permission: "Notification" in window ? Notification.permission : "unsupported",
        });
    }

    async onEnableBrowserNotifications() {
        if (!this.state.supported) {
            this.notification.add("This browser does not support native notifications.", {
                title: "CRM Sales Guard",
                type: "warning",
            });
            return;
        }
        this.state.permission = await Notification.requestPermission();
        if (this.state.permission === "granted") {
            this.notification.add("Native browser notifications are enabled.", {
                title: "CRM Sales Guard",
                type: "success",
            });
        } else {
            this.notification.add("Browser notification permission was not granted.", {
                title: "CRM Sales Guard",
                type: "warning",
            });
        }
    }
}

registry.category("systray").add("CrmSalesGuardSystray", {
    Component: CrmSalesGuardSystray,
}, { sequence: 45 });
