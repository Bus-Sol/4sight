odoo.define('l10n_mt.vat', function (require) {
"use strict";

var core = require('web.core');
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');

var VatController = ListController.extend({
    buttons_template: 'VatReport.buttons',
    events: _.extend({}, ListController.prototype.events, {
        'click .o_button_print_report': '_onPrintVat',
    }),

    _onPrintVat: function () {
        var self = this;
        $('.o_button_print_report').attr('disabled', true);
        console.log(self);
        return this._rpc({
            model: 'account.move.line',
            method: 'print_pdf',
            kwargs: {options : self.renderer.state.domain},
            context: self.initialState.context,
        })
        .then(function(result){
            var doActionProm = self.do_action(result);
            $('.o_button_print_report').attr('disabled', false);
            return doActionProm;
                })
        .guardedCatch(function() {
            $('.o_button_print_report').attr('disabled', false);
                });
    }
    });


    var VatListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: VatController,
        }),
    });

    viewRegistry.add('vat_report', VatListView);
});

odoo.define('l10n_mt.ActionManager', function (require) {
"use strict";

/**
 * The purpose of this file is to add the support of Odoo actions of type
 * 'ir_actions_sale_subscription_dashboard_download' to the ActionManager.
 */

var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');

ActionManager.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Executes actions of type 'ir_actions_sale_subscription_dashboard_download'.
     *
     * @private
     * @param {Object} action the description of the action to execute
     * @returns {Promise} resolved when the report has been downloaded ;
     *   rejected if an error occurred during the report generation
     */
    _executeVatDownloadAction: function (action) {
        var self = this;
        framework.blockUI();
        return new Promise(function (resolve, reject) {
            session.get_file({
                url: '/account_move_line',
                data: action.data,
                success: resolve,
                error: (error) => {
                    self.call('crash_manager', 'rpc_error', error);
                    reject();
                },
                complete: framework.unblockUI,
            });
        });
    },
    /**
     * Overrides to handle the 'ir_actions_sale_subscription_dashboard_download' actions.
     *
     * @override
     * @private
     */
    _handleAction: function (action, options) {
        if (action.type === 'ir_actions_vat_report_download') {
            return this._executeVatDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);
    },
});

});
