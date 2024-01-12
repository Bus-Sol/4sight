# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClientJobSheetInherits(models.Model):
    _inherit = 'client.jobsheet'

    @api.model
    def create(self, values):
        x_unit_amount = values.get('hours')
        x_str_unit_amount = str(x_unit_amount)
        x_split_unit_amount = x_str_unit_amount.split('.', 1)

        if len(x_split_unit_amount) > 1:
            x_str_unit_amount_after_float = x_split_unit_amount[1]

            if int(x_str_unit_amount_after_float) < 10 and '0' not in x_str_unit_amount_after_float:
                x_str_unit_amount_after_float = x_str_unit_amount_after_float + '0'

            x_int_unit_amount_after_float = int(x_str_unit_amount_after_float)
            if x_int_unit_amount_after_float > 60:
                raise ValidationError("Not Allowed To Enter Minutes Greater Then 60!")

        res = super().create(values)
        for rec in res:
            if rec.partner_id.x_timesheets_rounding:
                str_unit_amount = str(rec.hours)
                split_unit_amount = str_unit_amount.split('.', 1)
                print('ORIGINAL SPLIT UNIT AMOUNT IS ::: ', split_unit_amount)

                str_unit_amount_before_float = split_unit_amount[0]
                str_unit_amount_after_float = split_unit_amount[1]

                if int(str_unit_amount_after_float) < 10 and '0' not in str_unit_amount_after_float:
                    str_unit_amount_after_float = str_unit_amount_after_float + '0'

                int_unit_amount_before_float = int(str_unit_amount_before_float)
                int_unit_amount_after_float = int(str_unit_amount_after_float)

                if (int_unit_amount_after_float % 15) != 0:
                    print('NEEDS ROUNDING')
                    if 15 > int_unit_amount_after_float > 0:
                        int_unit_amount_after_float = 15
                    elif 30 > int_unit_amount_after_float > 15:
                        int_unit_amount_after_float = 30
                    elif 45 > int_unit_amount_after_float > 30:
                        int_unit_amount_after_float = 45
                    elif 60 > int_unit_amount_after_float > 45:
                        int_unit_amount_before_float += 1
                        int_unit_amount_after_float = 00

                    print('INT UNIT AMOUNT AFTER FLOAT IS ::: ', int_unit_amount_after_float)
                    str_unit_amount_to_save = str(str(int_unit_amount_before_float) + '.' + str(int_unit_amount_after_float))
                    print('STR UNIT AMOUNT TO SAVE IS ::: ', str_unit_amount_to_save)
                    print('FLOAT UNIT AMOUNT TO SAVE IS ::: ', float(str_unit_amount_to_save))
                    self.env.cr.execute("""UPDATE client_jobsheet SET hours=%s WHERE id=%s""", (float(str_unit_amount_to_save), rec.id))
                else:
                    print('NEEDS ROUNDING')
                    if int_unit_amount_after_float == 60:
                        int_unit_amount_before_float += 1
                        int_unit_amount_after_float = 00

                    print('INT UNIT AMOUNT AFTER FLOAT IS ::: ', int_unit_amount_after_float)
                    str_unit_amount_to_save = str(str(int_unit_amount_before_float) + '.' + str(int_unit_amount_after_float))
                    print('STR UNIT AMOUNT TO SAVE IS ::: ', str_unit_amount_to_save)
                    print('FLOAT UNIT AMOUNT TO SAVE IS ::: ', float(str_unit_amount_to_save))
                    self.env.cr.execute("""UPDATE client_jobsheet SET hours=%s WHERE id=%s""", (float(str_unit_amount_to_save), rec.id))
        return res

    def write(self, values):
        if values.get('hours'):
            for rec in self:
                if rec.partner_id.x_timesheets_rounding:
                    str_unit_amount = str(values.get('hours'))
                    split_unit_amount = str_unit_amount.split('.', 1)
                    print('ORIGINAL SPLIT UNIT AMOUNT IS ::: ', split_unit_amount)

                    str_unit_amount_before_float = split_unit_amount[0]
                    str_unit_amount_after_float = split_unit_amount[1]

                    if int(str_unit_amount_after_float) < 10 and '0' not in str_unit_amount_after_float:
                        str_unit_amount_after_float = str_unit_amount_after_float + '0'

                    int_unit_amount_before_float = int(str_unit_amount_before_float)
                    int_unit_amount_after_float = int(str_unit_amount_after_float)

                    if int_unit_amount_after_float > 60:
                        raise ValidationError("Not Allowed To Enter Minutes Greater Then 60!")

                    if (int_unit_amount_after_float % 15) != 0:
                        print('NEEDS ROUNDING')
                        if 15 > int_unit_amount_after_float > 0:
                            int_unit_amount_after_float = 15
                        elif 30 > int_unit_amount_after_float > 15:
                            int_unit_amount_after_float = 30
                        elif 45 > int_unit_amount_after_float > 30:
                            int_unit_amount_after_float = 45
                        elif 60 > int_unit_amount_after_float > 45:
                            int_unit_amount_before_float += 1
                            int_unit_amount_after_float = 00

                        print('INT UNIT AMOUNT AFTER FLOAT IS ::: ', int_unit_amount_after_float)
                        str_unit_amount_to_save = str(str(int_unit_amount_before_float) + '.' + str(int_unit_amount_after_float))
                        print('STR UNIT AMOUNT TO SAVE IS ::: ', str_unit_amount_to_save)
                        print('FLOAT UNIT AMOUNT TO SAVE IS ::: ', float(str_unit_amount_to_save))
                        values['hours'] = float(str_unit_amount_to_save)
                    else:
                        print('NEEDS ROUNDING')
                        if int_unit_amount_after_float == 60:
                            int_unit_amount_before_float += 1
                            int_unit_amount_after_float = 00

                        print('INT UNIT AMOUNT AFTER FLOAT IS ::: ', int_unit_amount_after_float)
                        str_unit_amount_to_save = str(str(int_unit_amount_before_float) + '.' + str(int_unit_amount_after_float))
                        print('STR UNIT AMOUNT TO SAVE IS ::: ', str_unit_amount_to_save)
                        print('FLOAT UNIT AMOUNT TO SAVE IS ::: ', float(str_unit_amount_to_save))
                        values['hours'] = float(str_unit_amount_to_save)

        res = super().write(values)
        return res


class AccountAnalyticLineInherits(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def create(self, values):
        x_unit_amount = values.get('unit_amount')
        x_str_unit_amount = str(x_unit_amount)
        x_split_unit_amount = x_str_unit_amount.split('.', 1)

        if len(x_split_unit_amount) > 1:
            x_str_unit_amount_after_float = x_split_unit_amount[1]

            if int(x_str_unit_amount_after_float) < 10 and '0' not in x_str_unit_amount_after_float:
                x_str_unit_amount_after_float = x_str_unit_amount_after_float + '0'

            x_int_unit_amount_after_float = int(x_str_unit_amount_after_float)
            if x_int_unit_amount_after_float > 60:
                raise ValidationError("Not Allowed To Enter Minutes Greater Then 60!")

        res = super().create(values)
        for rec in res:
            if rec.user_id.partner_id.x_timesheets_rounding:
                str_unit_amount = str(rec.unit_amount)
                split_unit_amount = str_unit_amount.split('.', 1)
                print('ORIGINAL SPLIT UNIT AMOUNT IS ::: ', split_unit_amount)

                str_unit_amount_before_float = split_unit_amount[0]
                str_unit_amount_after_float = split_unit_amount[1]

                if int(str_unit_amount_after_float) < 10 and '0' not in str_unit_amount_after_float:
                    str_unit_amount_after_float = str_unit_amount_after_float + '0'

                int_unit_amount_before_float = int(str_unit_amount_before_float)
                int_unit_amount_after_float = int(str_unit_amount_after_float)

                if (int_unit_amount_after_float % 15) != 0:
                    print('NEEDS ROUNDING')
                    if 15 > int_unit_amount_after_float > 0:
                        int_unit_amount_after_float = 15
                    elif 30 > int_unit_amount_after_float > 15:
                        int_unit_amount_after_float = 30
                    elif 45 > int_unit_amount_after_float > 30:
                        int_unit_amount_after_float = 45
                    elif 60 > int_unit_amount_after_float > 45:
                        int_unit_amount_before_float += 1
                        int_unit_amount_after_float = 00

                    print('INT UNIT AMOUNT AFTER FLOAT IS ::: ', int_unit_amount_after_float)
                    str_unit_amount_to_save = str(str(int_unit_amount_before_float) + '.' + str(int_unit_amount_after_float))
                    print('STR UNIT AMOUNT TO SAVE IS ::: ', str_unit_amount_to_save)
                    print('FLOAT UNIT AMOUNT TO SAVE IS ::: ', float(str_unit_amount_to_save))
                    self.env.cr.execute("""UPDATE account_analytic_line SET unit_amount=%s WHERE id=%s""", (float(str_unit_amount_to_save), rec.id))
                else:
                    print('NEEDS ROUNDING')
                    if int_unit_amount_after_float == 60:
                        int_unit_amount_before_float += 1
                        int_unit_amount_after_float = 00

                    print('INT UNIT AMOUNT AFTER FLOAT IS ::: ', int_unit_amount_after_float)
                    str_unit_amount_to_save = str(str(int_unit_amount_before_float) + '.' + str(int_unit_amount_after_float))
                    print('STR UNIT AMOUNT TO SAVE IS ::: ', str_unit_amount_to_save)
                    print('FLOAT UNIT AMOUNT TO SAVE IS ::: ', float(str_unit_amount_to_save))
                    self.env.cr.execute("""UPDATE account_analytic_line SET unit_amount=%s WHERE id=%s""", (float(str_unit_amount_to_save), rec.id))
        return res

    def write(self, values):
        if values.get('unit_amount'):
            for rec in self:
                if rec.user_id.partner_id.x_timesheets_rounding:
                    str_unit_amount = str(values.get('unit_amount'))
                    split_unit_amount = str_unit_amount.split('.', 1)
                    print('ORIGINAL SPLIT UNIT AMOUNT IS ::: ', split_unit_amount)

                    str_unit_amount_before_float = split_unit_amount[0]
                    str_unit_amount_after_float = split_unit_amount[1]

                    if int(str_unit_amount_after_float) < 10 and '0' not in str_unit_amount_after_float:
                        str_unit_amount_after_float = str_unit_amount_after_float + '0'

                    int_unit_amount_before_float = int(str_unit_amount_before_float)
                    int_unit_amount_after_float = int(str_unit_amount_after_float)

                    if int_unit_amount_after_float > 60:
                        raise ValidationError("Not Allowed To Enter Minutes Greater Then 60!")

                    if (int_unit_amount_after_float % 15) != 0:
                        print('NEEDS ROUNDING')
                        if 15 > int_unit_amount_after_float > 0:
                            int_unit_amount_after_float = 15
                        elif 30 > int_unit_amount_after_float > 15:
                            int_unit_amount_after_float = 30
                        elif 45 > int_unit_amount_after_float > 30:
                            int_unit_amount_after_float = 45
                        elif 60 > int_unit_amount_after_float > 45:
                            int_unit_amount_before_float += 1
                            int_unit_amount_after_float = 00

                        print('INT UNIT AMOUNT AFTER FLOAT IS ::: ', int_unit_amount_after_float)
                        str_unit_amount_to_save = str(str(int_unit_amount_before_float) + '.' + str(int_unit_amount_after_float))
                        print('STR UNIT AMOUNT TO SAVE IS ::: ', str_unit_amount_to_save)
                        print('FLOAT UNIT AMOUNT TO SAVE IS ::: ', float(str_unit_amount_to_save))
                        values['unit_amount'] = float(str_unit_amount_to_save)
                    else:
                        print('NEEDS ROUNDING')
                        if int_unit_amount_after_float == 60:
                            int_unit_amount_before_float += 1
                            int_unit_amount_after_float = 00

                        print('INT UNIT AMOUNT AFTER FLOAT IS ::: ', int_unit_amount_after_float)
                        str_unit_amount_to_save = str(str(int_unit_amount_before_float) + '.' + str(int_unit_amount_after_float))
                        print('STR UNIT AMOUNT TO SAVE IS ::: ', str_unit_amount_to_save)
                        print('FLOAT UNIT AMOUNT TO SAVE IS ::: ', float(str_unit_amount_to_save))
                        values['unit_amount'] = float(str_unit_amount_to_save)

        res = super().write(values)
        return res


class ResPartnerInherits(models.Model):
    _inherit = 'res.partner'

    x_timesheets_rounding = fields.Boolean(string='Timesheets Rounding?')
