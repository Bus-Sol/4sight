/** @odoo-module */

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

async function executeVatReportDownload({ env, action }) {
    env.services.ui.block();
    const url = "/vat_report_cy_download";
    const data = action.data;
    try {
      await download({ url, data });
    } finally {
      env.services.ui.unblock();
    }
}

registry
    .category("action_handlers")
    .add('ir_actions_vat_report_cy_download', executeVatReportDownload);
