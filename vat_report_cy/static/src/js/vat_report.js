odoo.define('vat_report_cy.ActionManager', function (require) {
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
    _executeVatCyDownloadAction: function (action) {
        var self = this;
        framework.blockUI();
        return new Promise(function (resolve, reject) {
            session.get_file({
                url: '/vat_report_cy_download',
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
        if (action.type === 'ir_actions_vat_report_cy_download') {
            return this._executeVatCyDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);
    },
});

});
