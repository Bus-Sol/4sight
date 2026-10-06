/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { useService } from "@web/core/utils/hooks";


export class VatController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notificationService = useService("notification");
    }
    async onVatReportClick() {
        var self = this;
        $('.o_button_print_report').attr('disabled', true);
        const action = await this.orm.call('account.move.line', 'print_pdf', [self.props.domain]);
        $('.o_button_print_report').attr('disabled', false);
        return this.actionService.doAction(action);
    }
};
registry.category('views').add('vat_report', {
    ...listView,
    Controller: VatController,
    buttonTemplate: 'vat_report_mt.buttons',
});