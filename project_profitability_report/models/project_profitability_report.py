from odoo import fields, models, tools


class ProjectProfitabilityReport(models.Model):
    _name = 'project.profitability.report'
    _description = 'Project Profitability Report'
    _auto = False
    _rec_name = 'project_id'
    _order = 'company_id, project_id'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        readonly=True,
    )

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        readonly=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        readonly=True,
    )

    user_id = fields.Many2one(
        'res.users',
        string='Project Manager',
        readonly=True,
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        readonly=True,
    )

    sale_amount = fields.Monetary(
        string='Confirmed Sales',
        readonly=True,
        currency_field='currency_id',
    )

    invoiced_revenue = fields.Monetary(
        string='Invoiced Revenue',
        readonly=True,
        currency_field='currency_id',
    )

    purchase_commitment = fields.Monetary(
        string='Purchase Commitments',
        readonly=True,
        currency_field='currency_id',
    )

    vendor_bill_cost = fields.Monetary(
        string='Vendor Bills',
        readonly=True,
        currency_field='currency_id',
    )

    timesheet_cost = fields.Monetary(
        string='Timesheet Cost',
        readonly=True,
        currency_field='currency_id',
    )

    expense_cost = fields.Monetary(
        string='Expenses',
        readonly=True,
        currency_field='currency_id',
    )

    total_cost = fields.Monetary(
        string='Total Cost',
        readonly=True,
        currency_field='currency_id',
    )

    margin = fields.Monetary(
        string='Margin',
        readonly=True,
        currency_field='currency_id',
    )

    margin_percent = fields.Float(
        string='Margin %',
        readonly=True,
        group_operator='avg',
    )

    def _query(self):
        return """
            WITH project_base AS (
                SELECT
                    p.id AS project_id,
                    p.analytic_account_id AS analytic_account_id,

                    COALESCE(
                        p.company_id,
                        so.company_id
                    ) AS company_id,

                    COALESCE(
                        p.partner_id,
                        so.partner_id
                    ) AS partner_id,

                    p.user_id,
                    sol.order_id AS sale_order_id,

                    COALESCE(
                        project_company.currency_id,
                        sale_company.currency_id
                    ) AS currency_id

                FROM project_project p

                LEFT JOIN sale_order_line sol
                    ON sol.id = p.sale_line_id

                LEFT JOIN sale_order so
                    ON so.id = sol.order_id

                LEFT JOIN res_company project_company
                    ON project_company.id = p.company_id

                LEFT JOIN res_company sale_company
                    ON sale_company.id = so.company_id

                WHERE p.active IS TRUE
            ),

            sales AS (
                SELECT
                    so.id AS sale_order_id,
                    so.amount_untaxed AS sale_amount
                FROM sale_order so
                WHERE so.state IN ('sale', 'done')
            ),

            invoice_revenue AS (
                SELECT
                    pb.project_id,
                    SUM(-aml.balance) AS invoiced_revenue

                FROM project_base pb

                JOIN account_move_line aml
                    ON pb.analytic_account_id IS NOT NULL
                    AND COALESCE(
                        aml.analytic_distribution,
                        '{}'::jsonb
                    ) ? pb.analytic_account_id::text

                JOIN account_move am
                    ON am.id = aml.move_id

                JOIN account_account aa
                    ON aa.id = aml.account_id

                WHERE am.state = 'posted'
                  AND am.move_type IN (
                      'out_invoice',
                      'out_refund'
                  )
                  AND aa.account_type = 'income'
                  AND aml.display_type = 'product'

                GROUP BY pb.project_id
            ),

            purchase_commitments AS (
                SELECT
                    pb.project_id,
                    SUM(pol.price_subtotal) AS purchase_commitment

                FROM project_base pb

                JOIN purchase_order_line pol
                    ON pb.analytic_account_id IS NOT NULL
                    AND COALESCE(
                        pol.analytic_distribution,
                        '{}'::jsonb
                    ) ? pb.analytic_account_id::text

                JOIN purchase_order po
                    ON po.id = pol.order_id

                WHERE po.state IN ('purchase', 'done')
                  AND pol.display_type IS NULL

                GROUP BY pb.project_id
            ),

            vendor_bills AS (
                SELECT
                    pb.project_id,
                    SUM(aml.balance) AS vendor_bill_cost

                FROM project_base pb

                JOIN account_move_line aml
                    ON pb.analytic_account_id IS NOT NULL
                    AND COALESCE(
                        aml.analytic_distribution,
                        '{}'::jsonb
                    ) ? pb.analytic_account_id::text

                JOIN account_move am
                    ON am.id = aml.move_id

                JOIN account_account aa
                    ON aa.id = aml.account_id

                WHERE am.state = 'posted'
                  AND am.move_type IN (
                      'in_invoice',
                      'in_refund'
                  )
                  AND aa.account_type IN (
                      'expense',
                      'expense_depreciation',
                      'expense_direct_cost'
                  )
                  AND aml.display_type = 'product'

                GROUP BY pb.project_id
            ),

            timesheets AS (
                SELECT
                    aal.account_id AS analytic_account_id,

                    SUM(
                        CASE
                            WHEN aal.amount < 0
                                THEN -aal.amount
                            ELSE 0.0
                        END
                    ) AS timesheet_cost

                FROM account_analytic_line aal

                WHERE aal.project_id IS NOT NULL
                  AND aal.account_id IS NOT NULL
                  AND aal.amount < 0

                GROUP BY aal.account_id
            ),

            expenses AS (
                SELECT
                    pb.project_id,

                    SUM(
                        CASE
                            WHEN aal.amount < 0
                                THEN -aal.amount
                            ELSE 0.0
                        END
                    ) AS expense_cost

                FROM project_base pb

                JOIN account_analytic_line aal
                    ON pb.analytic_account_id IS NOT NULL
                    AND aal.account_id = pb.analytic_account_id

                WHERE aal.amount < 0
                  AND aal.project_id IS NULL
                  AND aal.employee_id IS NOT NULL
                  AND aal.move_line_id IS NOT NULL

                GROUP BY pb.project_id
            )

            SELECT
                pb.project_id AS id,
                pb.project_id,
                pb.analytic_account_id,
                pb.company_id,
                pb.currency_id,
                pb.partner_id,
                pb.user_id,
                pb.sale_order_id,

                COALESCE(
                    s.sale_amount,
                    0.0
                ) AS sale_amount,

                COALESCE(
                    ir.invoiced_revenue,
                    0.0
                ) AS invoiced_revenue,

                COALESCE(
                    pc.purchase_commitment,
                    0.0
                ) AS purchase_commitment,

                COALESCE(
                    vb.vendor_bill_cost,
                    0.0
                ) AS vendor_bill_cost,

                COALESCE(
                    ts.timesheet_cost,
                    0.0
                ) AS timesheet_cost,

                COALESCE(
                    ex.expense_cost,
                    0.0
                ) AS expense_cost,

                (
                    COALESCE(vb.vendor_bill_cost, 0.0)
                    + COALESCE(ts.timesheet_cost, 0.0)
                    + COALESCE(ex.expense_cost, 0.0)
                ) AS total_cost,

                (
                    COALESCE(ir.invoiced_revenue, 0.0)
                    - COALESCE(vb.vendor_bill_cost, 0.0)
                    - COALESCE(ts.timesheet_cost, 0.0)
                    - COALESCE(ex.expense_cost, 0.0)
                ) AS margin,

                CASE
                    WHEN ABS(
                        COALESCE(ir.invoiced_revenue, 0.0)
                    ) > 0.000001
                    THEN (
                        (
                            COALESCE(ir.invoiced_revenue, 0.0)
                            - COALESCE(vb.vendor_bill_cost, 0.0)
                            - COALESCE(ts.timesheet_cost, 0.0)
                            - COALESCE(ex.expense_cost, 0.0)
                        )
                        / ABS(
                            COALESCE(ir.invoiced_revenue, 0.0)
                        )
                    ) * 100.0
                    ELSE 0.0
                END AS margin_percent

            FROM project_base pb

            LEFT JOIN sales s
                ON s.sale_order_id = pb.sale_order_id

            LEFT JOIN invoice_revenue ir
                ON ir.project_id = pb.project_id

            LEFT JOIN purchase_commitments pc
                ON pc.project_id = pb.project_id

            LEFT JOIN vendor_bills vb
                ON vb.project_id = pb.project_id

            LEFT JOIN timesheets ts
                ON ts.analytic_account_id = pb.analytic_account_id

            LEFT JOIN expenses ex
                ON ex.project_id = pb.project_id
        """

    def init(self):
        tools.drop_view_if_exists(
            self.env.cr,
            self._table,
        )

        self.env.cr.execute(
            f"""
                CREATE OR REPLACE VIEW {self._table} AS (
                    {self._query()}
                )
            """
        )

    def action_open_sales_order(self):
        self.ensure_one()

        if not self.sale_order_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }

    def action_open_project(self):
        self.ensure_one()

        if not self.project_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Project',
            'res_model': 'project.project',
            'view_mode': 'form',
            'res_id': self.project_id.id,
            'target': 'current',
        }

    def action_open_analytic_items(self):
        self.ensure_one()

        if not self.analytic_account_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Analytic Items',
            'res_model': 'account.analytic.line',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [
                (
                    'account_id',
                    '=',
                    self.analytic_account_id.id,
                ),
            ],
            'context': {
                'search_default_group_by_date': 1,
            },
            'target': 'current',
        }
