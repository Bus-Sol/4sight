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
        this.fieldRequiredInput = this.$('input[name="field_required"]');

        console.log('contactTypeSelect', this.contactTypeSelect)
        console.log('companyFields', this.companyFields)
        this._updateFieldVisibility(this.contactTypeSelect.val());



        // if (document.getElementById("company_type")) {
        //     this._onChangeCompanyType();
        // }
        return this._super.apply(this, arguments);
    },



    _updateFieldVisibility: function (companyType) {
        const isCompany = companyType === 'company';

        // 1. Toggle field visibility
        this.individualFields.toggle(!isCompany);
        this.companyFields.toggle(isCompany);

        // 2. Toggle the label for 'name' field
        const nameLabel = this.$('label[for="name"] span');
        if (isCompany) {
            nameLabel.text('Company Name');
        } else {
            nameLabel.text('Full name');
        }

        // 3. Update the hidden field_required input for server-side validation
        if (isCompany) {
            this.fieldRequiredInput.val('name,street,city,country_id,vat,phone,email');
        } else {
            this.fieldRequiredInput.val('firstname,lastname,phone,email');
        }
    },



     _onChangeCompanyType: function(ev) {
        const companyType = document.querySelector('select[name="company_type"]');
        const targetValue = ev.currentTarget.value
        console.log('companyType', companyType)
        console.log('targetValue', targetValue)
        var is_company =  targetValue === 'company'

        this._updateFieldVisibility(targetValue);

//        this.individualFields.toggle(!is_company);
//        this.companyFields.toggle(is_company);

    },


});
