# -*- coding: utf-8 -*-
from odoo import fields, models, api, modules, _

CATEGORY = [('lefkosia','Lefkosia District'),
            ('larnaka','Larnaka District'),
            ('lemesos','Lemesos Districtt'),
            ('pafos','Pafos District'),
            ('ammochostos','Ammochostos District'),
            ('occupied-areas','Occupied Areas'),
            ('government-authorities','Government Authorities'),
            ('post-office-boxes','Post Office Boxes'),
            ('parcel24','Parcel24'),
            ]

class CrmLead(models.Model):
    _inherit = "crm.lead"

    first_name = fields.Char("First Name")
    father_name = fields.Char("Father's name")
    surname = fields.Char('Surname')
    dob = fields.Date('Date of birth')
    place_of_birth = fields.Char('Place of birth')
    country_birth = fields.Char('Country of birth')
    citizenship = fields.Char('Citizenship')
    martial_status = fields.Selection([('d','Divorced'),('m','Married'),('s','Single'),('w','Widow/Widower')],string='Marital status')
    educational_level = fields.Selection([('p','Primary'),('s','Secondary '),('t','Tertiary')],string='Educational Level')
    flat_num = fields.Char('Flat No.')
    house_name = fields.Char('House Name')
    street = fields.Char('Street')
    street_number = fields.Char('Street Number')
    postal_code = fields.Char('Postal Code')
    district_id = fields.Many2one('cyprus.district')
    area_domain = fields.Many2many('cyprus.area', compute='compute_area_domain')
    city_town_id = fields.Many2one('cyprus.area' ,string='Community/Area', domain="[('id', 'in', area_domain)]")
    country = fields.Char('Country')
    flat_num_2 = fields.Char('Flat No.')
    house_name_2 = fields.Char('House Name')
    street_2 = fields.Char('Street')
    street_number_2 = fields.Char('Street Number')
    postal_code_2 = fields.Char('Postal Code')
    district_2 = fields.Selection(CATEGORY)
    city_town_2 = fields.Char('City / Town')
    country_2 = fields.Char('Country')
    national_id_number = fields.Char('National ID Number')
    national_id_insurrance_number = fields.Char('National ID Issuance Country')
    national_id_insurrance_date = fields.Date('National ID Issuance Date')
    national_id_expiration_date = fields.Date('National ID Expiration Date')
    passport_number = fields.Char('Passport Number')
    passport_insurrance_country = fields.Char('Passport Issuance Country')
    passport_insurrance_date = fields.Date('Passport Issuance Date')
    passport_expiration_date = fields.Date('Passport Expiration Date')
    profession = fields.Char('Profession')
    title_position = fields.Char('Title/ Position')
    employes_name = fields.Char('Employer’s Name')
    annual_gross_income = fields.Char('Annual gross income')
    work_address = fields.Char('Work address')
    post_code = fields.Char('Post code')
    business_phone_number = fields.Char('Business phone number')
    business_email_address = fields.Char('Business Email Address')
    employement_status_1 = fields.Selection([('m', 'Minor'), ('ft', 'Full Time'), ('se', 'Self Employed'),('ph', 'PartTime/ Housewife')],string="Private Status Type")
    employement_status_2 = fields.Selection([('private_s', 'Private Sector'), ('public_s', 'Public Sector'),('semi_gov_s', 'Semi-Government Sector'),('businessman', 'Businessman')],string="Type of Sector")
    employement_status_3 = fields.Selection(
        [('military_service', 'Military Service'), ('student', 'Student'), ('pensioner', 'Pensioner'),
         ('unemployed', 'Unemployed')], string="Employment Status")
    mobile_number = fields.Char('Mobile number')
    home_phone_number = fields.Char('Home Phone Number')
    fax_number = fields.Char('Fax number')
    personal_email_1 = fields.Char('Personal E-mail 1')
    personal_email_2 = fields.Char('Personal E-mail 2')
    acc_exp_credit_turnover = fields.Char('Account’s expected credit turnover (annually)')
    is_saving = fields.Boolean('Savings')
    is_product_needs = fields.Boolean('Product needs')
    is_payroll = fields.Boolean('Payroll')
    is_personal_noncommercial_trx = fields.Boolean('Personal non-commercial transactions')
    is_trade_finance_trx = fields.Boolean('Trade finance transactions')
    is_domestic_trx_business = fields.Boolean('Domestic transactions / business')
    is_crossborder_trx_business = fields.Boolean('Cross border transactions/ business')
    is_cash = fields.Boolean('Cash')
    is_cheques = fields.Boolean('Cheques')
    is_domestic_transfers = fields.Boolean('Domestic Transfers')
    is_mutual_funds = fields.Boolean('Mutual Funds')
    is_crossborder_incom_trans = fields.Boolean('Cross Border Incoming Transfers')
    is_crossborder_outward_trans = fields.Boolean('Cross Border Outward Transfers')
    is_outward_domestic_trans = fields.Boolean('Outward Domestic transfers')
    is_stocks = fields.Boolean('Stocks')
    is_credit_card = fields.Boolean('Credit Cards')
    inward_transfers = fields.Char('For inward transfers')
    outward_transfers = fields.Char('For outward transfers')
    is_business_activity = fields.Boolean('Business Activity')
    is_investment_activity = fields.Boolean('Investment Activity')
    is_salary_pension = fields.Boolean('Salary/Pensions')
    is_earnings_sop = fields.Boolean('Earnings (Sale of Property)')
    is_earnings_sob = fields.Boolean('Earnings (Sale of Business)')
    is_earnings_soi = fields.Boolean('Earnings (Sale of Investments)')
    is_inheritance = fields.Boolean('Inheritance')
    is_divorce_settlement = fields.Boolean('Divorce Settlement')
    is_insurance_proceeds_settlement = fields.Boolean('Insurance Proceeds/ Settlement')
    is_winning_ngl = fields.Boolean('Winnings (Non-Government Lottery)')
    is_winning_gl = fields.Boolean('Winnings (Government Lottery)')
    ba_line_of_bd = fields.Char('Business Activity / Line of Business Details')

    @api.depends('district_id')
    def compute_area_domain(self):
        domain = [('id', 'in', self.env['cyprus.area'].search([('district_name','=',self.district_id.key)]).ids)] if self.district_id else [('id', '=', False)]
        self.area_domain = self.env['cyprus.area'].search(domain)

    @api.onchange('district_id')
    def onchange_district_id(self):
        if self.district_id:
            self.city_town_id = False
