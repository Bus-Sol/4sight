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

        this.contactTypeSelect = this.$('#company_type');
        // this.individualFields = this.$('.o_individual_field');
        // this.companyFields = this.$('.o_company_field');
        this.fieldRequiredInput = this.$('input[name="field_required"]');

        console.log('contactTypeSelect', this.contactTypeSelect.val())
        console.log('fieldRequiredInput', this.fieldRequiredInput.val())


        const isCompany = this.contactTypeSelect.val() === 'company';
        if (isCompany) {
            this.fieldRequiredInput.val('name,street,city,country_id,vat,phone,email, privacy_terms');
        } else {
            this.fieldRequiredInput.val('firstname,lastname,phone,email, privacy_terms');
        }





        console.log('fieldRequiredInput', this.fieldRequiredInput.val())
        // if (document.getElementById("company_type")) {
        //     this._onChangeCompanyType();
        // }
        return this._super.apply(this, arguments);
    },


    _updateFieldVisibility: function (companyType) {
        const isCompany = companyType === 'company';
        const $container = this.$('.o_website_sale_address_form');

        // 1. Switch the parent class (CSS does the rest)
        $container.toggleClass('o_state_company', isCompany);
        $container.toggleClass('o_state_individual', !isCompany);

        // 2. Handle the Label
        const nameLabel = this.$('label[for="name"] span');
        nameLabel.text(isCompany ? 'Company Name' : 'Full name');

        // 3. Update required fields
        const fieldRequiredInput = this.$('input[name="field_required"]');
        if (fieldRequiredInput.length) {
            fieldRequiredInput.val(isCompany ?
                'name,street,city,country_id,vat,zip,phone,email' :
                'firstname,lastname,phone,email'
            );
        }
    },

    _onChangeCompanyType: function(ev) {
        this._updateFieldVisibility($(ev.currentTarget).val());
    },
});