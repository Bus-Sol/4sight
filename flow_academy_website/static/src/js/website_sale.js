/** @odoo-module **/
import { WebsiteSale } from "@website_sale/js/website_sale";

WebsiteSale.include({
    events: Object.assign(WebsiteSale.prototype.events, {
        'change select[name="company_type"]': "_onChangeCompanyType",
    }),
    /**
     * @override
     */
    start() {
        const def = this._super(...arguments);
        if (document.getElementById("company_type")) {
            this._onChangeCompanyType();
        }
        return def;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------
    /**
     * Event click, hidden fields l10n_cl_activity_description
     * if l10n_cl_sii_taxpayer_type is 'ticket'
     *
     * @private
     */


     _onChangeCompanyType: function(ev) {
        const selectedIdentificationType = ev.currentTarget.options[ev.currentTarget.selectedIndex].text

        if (selectedIdentificationType === "NIT") {
            this.obligationTypeBlock.classList.remove("d-none");
            this.fiscalRegimenBlock.classList.remove("d-none");
        } else {
            this.obligationTypeBlock.classList.add("d-none");
            this.fiscalRegimenBlock.classList.add("d-none");
        }
    },

    _onChangeCompanyType() {
        const typeDocumentEl = document.querySelector('input[name="l10n_cl_type_document"]');
        const checked = typeDocumentEl.checked ? "none" : "flex";
        document.getElementById("div_l10n_cl_additional_fields").style.display = checked;
    },
});
