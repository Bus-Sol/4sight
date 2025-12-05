/** @odoo-module **/
import { WebsiteSale } from "@website_sale/js/website_sale";

WebsiteSale.include({
    events: Object.assign(WebsiteSale.prototype.events, {
        'change select[name="company_type"]': "_onChangeCompanyType",
    }),
    /**
     * @override
     */
    init() {
        this._super(...arguments);

    },

    start() {

        this.contactTypeSelect = this.$('#company_type');
        this.individualFields = this.$('.o_individual_field');
        this.companyFields = this.$('.o_company_field');

        console.log('contactTypeSelect', this.contactTypeSelect)
        console.log('companyFields', this.companyFields)



        // if (document.getElementById("company_type")) {
        //     this._onChangeCompanyType();
        // }
        return this._super.apply(this, arguments);
    },




     _onChangeCompanyType: function(ev) {
        const companyType = document.querySelector('select[name="company_type"]');
        const targetValue = ev.currentTarget.value
        console.log('companyType', companyType)
        console.log('targetValue', targetValue)
        var is_company =  targetValue === 'company'

        this.individualFields.toggle(!is_company);
        this.companyFields.toggle(is_company);

    },


});
