/** @odoo-module */

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

async function executeAccountReportDownload({ env, action }) {
    env.services.ui.block();
    const url = "/account_move_line";
    const data = action.data;
    try {
      await download({ url, data });
    } finally {
      env.services.ui.unblock();
    }
}

registry
    .category("action_handlers")
    .add('ir_actions_vat_report_download', executeAccountReportDownload);
