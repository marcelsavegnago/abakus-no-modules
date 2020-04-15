# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import datetime
import logging
_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], 'Subscription type', required=True, default='sale')

    contract_team = fields.Many2one('account.analytic.account.team', string="Team")
    resource_calendar_id = fields.Many2one('resource.calendar', string="Working Time")
    invoicable_factor_inside_calendar = fields.Many2one('hr_timesheet_invoice.factor', string='Default invoicable factor during calendar')
    invoicable_factor_outside_calendar = fields.Many2one('hr_timesheet_invoice.factor', string='Default invoicable factor outside calendar')

    contract_type_product_name = fields.Char(related='template_id.timesheet_product.name', string="Product name")
    timesheets_count = fields.Integer(compute='compute_timesheets_count', string="Timesheet count")

    total_invoice_amount = fields.Float(compute='_compute_total_invoice_amount', string="Total invoice amount", store=True)
    total_timesheet_to_invoice = fields.Float(compute='_compute_total_invoice_amount', string="Total Timesheet To Invoice", store=True)
    computed_units_consumed = fields.Float(compute='_compute_units_consumed', string="Units Consumed", store=False)
    computed_units_remaining = fields.Float(compute='_compute_units_remaining', string="Units Remaining", store=False)
    total_invoice_amount_info = fields.Char(compute='_compute_total_invoice_amount_info', string="Total invoice amount", store=False)
    consumption_percentage = fields.Float(string="Consumption", help="Percentage of the used time vs prepaid time")

    timesheet_product_price = fields.Float("Hourly Rate")
    contractual_minimum_amount = fields.Float(string="Contractual minimum amount")
    contractual_minimum_quantity = fields.Float(string="Contractual minimum quantity")
    minimum_invoicable_quantity = fields.Float(string="Minimum Invoicable Quantity", default="0.25")
    use_project = fields.Boolean(string="Use Project")
    project_id = fields.Many2one('project.project', string="Project")
    contractual_factor = fields.Float(string="Contractual TS Factor", help="The time spent on timesheets will be multiplied by this number.", default=1)
    journal_id = fields.Many2one('account.journal', string="Accounting Journal")

    state = fields.Selection([('negociation','Negociation'),
                              ('draft','New'),
                              ('open','In Progress'),
                              ('pending','To Renew'),
                              ('close','Closed'),
                              ('cancel', 'Cancelled'),
                              ('refused','Refused')], default='draft')
    
    last_recompute_date = fields.Datetime(string='Last Recompute Date')

    invoice_contract_type = fields.Selection(related='template_id.invoice_contract_type')
    description_needed = fields.Boolean(related='template_id.description_needed')
    technical_description = fields.Text(string="Technical description")
    supplier_needed = fields.Boolean(related='template_id.supplier_needed')
    supplier_id = fields.Many2one('res.partner', string="Supplier for this contract")
    subscription_start_date_needed = fields.Boolean(related='template_id.subscription_start_date_needed')
    subscription_start_date = fields.Date(string="Service Start Date")
    subscription_end_date_needed = fields.Boolean(related='template_id.subscription_end_date_needed')
    subscription_end_date = fields.Date(string="Service End Date")

    task_ids = fields.One2many('project.task', string="Tasks", related='project_id.task_ids')
    tasks_count = fields.Integer(string="Tasks count", compute='compute_tasks_count')

    @api.multi
    @api.depends('task_ids')
    def compute_tasks_count(self):
        for sub in self:
            sub.tasks_count = len(sub.task_ids)

    @api.multi
    def _compute_units_consumed(self):
        for sub in self:
            total = 0
            for line in sub.analytic_account_id.line_ids.filtered(lambda r: r.is_timesheet == True):
                total += (line.invoicable_unit_amount * sub.contractual_factor)
            sub.computed_units_consumed = total

    @api.multi
    def _compute_units_remaining(self):
        for sub in self:
            sub.computed_units_remaining = sub.contractual_minimum_amount - sub.computed_units_consumed


    @api.multi
    @api.onchange('template_id')
    def changed_template_id(self):
        for subscription in self:
            if subscription.template_id:
                # Set Invoice Lines
                subscription.recurring_invoice_line_ids.unlink()
                for template_line in subscription.template_id.subscription_line_ids:
                    line = self.env['sale.subscription.line'].create({
                        'product_id': template_line.product_id.id,
                        'name': template_line.name,
                        'quantity': template_line.quantity,
                        'uom_id': template_line.uom_id.id,
                        'price_unit': template_line.price_unit,
                        'discount': template_line.discount,
                        'price_subtotal': template_line.price_subtotal,
                    })
                    line.analytic_account_id = subscription
                    line.onchange_product_id()
                    line.onchange_product_quantity()
                    line.onchange_uom_id()

                if (subscription.type == 'sale'):
                    # Use project
                    subscription.use_project = subscription.template_id.use_project
                    # Timesheet product price
                    subscription.timesheet_product_price = subscription.template_id.timesheet_product.lst_price
                    # Product name
                    subscription.contract_type_product_name = subscription.template_id.timesheet_product.name
                    # Contractual minimum quantity
                    subscription.contractual_minimum_quantity = subscription.template_id.contractual_minimum_quantity
                    # Contractual minimum amount
                    subscription.contractual_minimum_amount = subscription.template_id.contractual_minimum_amount
                    # Minimum invoicable quantity
                    subscription.minimum_invoicable_quantity = subscription.template_id.minimum_invoicable_quantity
                    # Contract Team
                    subscription.contract_team = subscription.template_id.contract_team
                    # Working calendar
                    subscription.resource_calendar_id = subscription.template_id.resource_calendar_id
                    # Invoicing factors
                    subscription.invoicable_factor_inside_calendar = subscription.template_id.invoicable_factor_inside_calendar
                    subscription.invoicable_factor_outside_calendar = subscription.template_id.invoicable_factor_outside_calendar
                    # Journal
                    subscription.journal_id = subscription.template_id.journal_id
                else:
                    # Reset the subscription
                    subscription.use_project = False
                    subscription.timesheet_product_price = 0
                    subscription.contract_type_product_name = ""
                    subscription.contractual_minimum_amount = 0
                    subscription.minimum_invoicable_quantity = 0
                    subscription.contractual_minimum_quantity = 0
                    subscription.contract_team = False
                    subscription.resource_calendar_id = False
                    subscription.invoicable_factor_inside_calendar = False
                    subscription.invoicable_factor_outside_calendar = False
                    subscription.journal_id = False


    @api.model
    def create(self, values):
        if 'analytic_account_id' not in values or values['analytic_account_id'] == False:
            analytic_account_id = self.env['account.analytic.account'].create({
                'name': values['code'],
                'partner_id': values['partner_id'],
                'code': values['code'],
            })
            values.update({
                'analytic_account_id': analytic_account_id.id,
            })

        res = super(SaleSubscription, self).create(values)
        self.create_project_if_needed()

        return res

    @api.multi
    def write(self, values):
        res = super(SaleSubscription, self).write(values)
        if not self.analytic_account_id:
            if self.project_id and self.project_id.analytic_account_id:
                self.analytic_account_id = self.project_id.analytic_account_id
            else:
                self.analytic_account_id = self.env['account.analytic.account'].create({
                    'name': self.code,
                    'partner_id': self.partner_id.id,
                    'code': self.code,
                })

        self.create_project_if_needed()
        return res

    @api.multi
    def create_project_if_needed(self):
        for sub in self:
            # Only check this on sale contract
            if sub.type == 'sale' and sub.use_project and  not sub.project_id:
                # Create a project using the project template on the contract type
                sub.project_id = sub.template_id.project_template_id.copy({
                    'name': sub.code,
                    'user_id': sub.user_id.id,
                    'partner_id': sub.partner_id.id,
                    'resource_calendar_id': sub.resource_calendar_id.id,
                    'analytic_account_id': sub.analytic_account_id.id,
                    'sale_subscription_id': sub.id,
                })

    @api.multi
    def compute_timesheets_count(self):
        for sub in self:
            sub.timesheets_count = len(sub.analytic_account_id.line_ids.filtered(lambda r: r.is_timesheet))

    @api.multi
    def recompute_total_invoice_amount(self):
        for sub in self:
            sub._compute_total_invoice_amount()

    @api.multi
    @api.onchange('template_id', 'contractual_factor')
    @api.depends('analytic_account_id.line_ids', 'contractual_factor')
    def _compute_total_invoice_amount(self):
        for sub in self:
            service_delivery_total = 0
            total_travel_count = 0
            invoiced_travel_count = 0
            prepaid_installment_total = 0
            travel_price = sub.on_site_product.lst_price if not sub.on_site_invoice_by_km else (sub.on_site_product.lst_price * sub.on_site_distance_in_km)

            for line in sub.analytic_account_id.line_ids:
                # check if invoice exists for the current line, so it's a line related to the prepaid installment
                if line.move_id:
                    computed_amount = line.amount
                    prepaid_installment_total += computed_amount
                    # Check if on_site invoice line
                    if line.product_id == sub.on_site_product:
                        invoiced_travel_count += line.unit_amount

                # If line is not related to invoice, it's related to timesheet
                else:
                    # If line is On-site
                    if line.on_site:
                        total_travel_count += 1

                    # Check if the min invoicable is correct
                    if line.unit_amount < sub.minimum_invoicable_quantity:
                        line.invoicable_unit_amount = sub.minimum_invoicable_quantity

                    # Check if TS was made during the resource calendar, if not, apply another contractual_factor
                    line.is_outside_resource_calendar = not sub.is_date_in_resource_calendar(line.date_begin, sub.resource_calendar_id)

                    # Invoice factor
                    invoice_factor = line.to_invoice
                    if line.is_outside_resource_calendar:
                        invoice_factor = sub.invoicable_factor_outside_calendar
                    # Set correct line amount
                    line.amount = ((sub.timesheet_product_price * line.invoicable_unit_amount * sub.contractual_factor) * ((100 - invoice_factor.factor) / 100))

                    # Sum service delivery
                    service_delivery_total += line.amount

            # Set total_timesheet_to_invoice
            sub.total_timesheet_to_invoice = (service_delivery_total - prepaid_installment_total) + (invoiced_travel_count * travel_price)

            # total_invoicable
            total_invoicable = service_delivery_total + (total_travel_count * travel_price)

            # Set %age
            sub.total_invoice_amount = round(prepaid_installment_total - total_invoicable, 2)
            if sub.contractual_minimum_amount != 0:
                sub.consumption_percentage = int((total_invoicable / sub.contractual_minimum_amount) * 100)
            else:
                sub.consumption_percentage = 0

            # Set last compute date
            sub.last_recompute_date = fields.Datetime.now()

    @api.multi
    @api.onchange('template_id')
    @api.depends('analytic_account_id.line_ids')
    def _compute_total_invoice_amount_info(self):
        for sub in self:
            balance = sub.total_invoice_amount
            if balance >= 0:
                info = 'In favour of the customer'
            if balance < 0:
                info = 'In favour of ' + sub.company_id.name
            sub.total_invoice_amount_info = str(abs(balance))+' '+u"\u20AC"+" ("+info+")" # u20AC == euro sign
            sub.last_recompute_date = fields.Datetime.now()

    def _prepare_adjustment_invoice_lines(self, fiscal_position):
        self.ensure_one()
        lines = []

        fiscal_position = self.env['account.fiscal.position'].browse(fiscal_position)

        # Create a line for the extra time consumption
        quantity_time = float(self.total_timesheet_to_invoice / self.timesheet_product_price)

        account = self.template_id.timesheet_product.property_account_income_id
        if not account:
            account = self.template_id.timesheet_product.categ_id.property_account_income_categ_id
        account_id = fiscal_position.map_account(account).id

        tax = self.template_id.timesheet_product.taxes_id.filtered(lambda r: r.company_id == self.company_id)
        tax = fiscal_position.map_tax(tax, product=self.template_id.timesheet_product, partner=self.partner_id)

        lines.append((0, 0, {
            'name': self.template_id.timesheet_product.name,
            'account_id': account_id,
            'account_analytic_id': self.analytic_account_id.id,
            'subscription_id': self.id,
            'price_unit' : self.timesheet_product_price,
            'discount': 0.0,
            'quantity': quantity_time,
            'uom_id': self.template_id.timesheet_product.uom_id.id,
            'product_id': self.template_id.timesheet_product.id,
            'invoice_line_tax_ids': [(6, 0, tax.ids)],
            'analytic_tag_ids': [(6, 0, self.analytic_account_id.tag_ids.ids)]
        }))

        # Create a line for the travel costs
        on_site_price = self.on_site_product.lst_price if not self.on_site_invoice_by_km else (self.on_site_product.lst_price * self.on_site_distance_in_km)
        quantity_on_site = (abs(self.total_invoice_amount) - self.total_timesheet_to_invoice) / on_site_price
        if quantity_on_site > 0:

            account = self.on_site_product.property_account_income_id
            if not account:
                account = self.on_site_product.categ_id.property_account_income_categ_id
            account_id = fiscal_position.map_account(account).id

            tax = self.on_site_product.taxes_id.filtered(lambda r: r.company_id == self.company_id)
            tax = fiscal_position.map_tax(tax, product=self.on_site_product, partner=self.partner_id)

            lines.append((0, 0, {
                'name': self.on_site_product.name,
                'account_id': account_id,
                'account_analytic_id': self.analytic_account_id.id,
                'subscription_id': self.id,
                'price_unit' : on_site_price,
                'discount': 0.0,
                'quantity': quantity_on_site,
                'uom_id': self.on_site_product.uom_id.id,
                'product_id': self.on_site_product.id,
                'invoice_line_tax_ids': [(6, 0, tax.ids)],
                'analytic_tag_ids': [(6, 0, self.analytic_account_id.tag_ids.ids)]
            }))

        return lines


    def create_invoice(self):
        self.ensure_one()
        account_analytic_lines = self.analytic_account_id.line_ids.filtered(lambda r: r.invoice_id == False)

        if self.total_invoice_amount < 0:

            invoice_data = self._prepare_invoice_data()
            invoice_data['comment'] = _('Ajustment Invoice')
            invoice_data['invoice_line_ids'] = self._prepare_adjustment_invoice_lines(invoice_data['fiscal_position_id'])
            invoice_id = self.env['account.invoice'].create(invoice_data)

            account_analytic_lines.write({'invoice_id': invoice_id.id})

            # Compute the taxes and total of the invoice
            invoice_id.compute_taxes()
            invoice_id._compute_amount()

            action = self.env.ref('account.action_invoice_tree1').read()[0]
            action["context"] = {"create": False}
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoice_id.id

            return action

    def is_date_in_resource_calendar(self, date_time, resource_calendar_id):
        date_time = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
        lines = resource_calendar_id.attendance_ids.filtered(lambda a: int(a.dayofweek) == int(date_time.weekday()))
        hour = date_time.hour + date_time.minute / 60.0
        for line in lines:
            if line.hour_from <= hour <= line.hour_to:
                return True
        return False

    # Inherit this method to only show invoices that are related to this subscription
    # based on their Analytic Account. If left as default, invoices with no reference will
    # be taken also because it's also based on reference.
    @api.multi
    def action_subscription_invoice(self):
        analytic_ids = [sub.analytic_account_id.id for sub in self]
        invoices = self.env['account.invoice'].search([('invoice_line_ids.account_analytic_id', 'in', analytic_ids)])
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.invoice",
            "views": [[self.env.ref('account.invoice_tree').id, "tree"],
                      [self.env.ref('account.invoice_form').id, "form"]],
            "domain": [["id", "in", invoices.ids]],
            "context": {"create": False},
            "name": "Invoices",
        }

    # Action to show timesheet lines for the current subscription
    def action_subscription_timesheet(self):
        analytic_ids = [sub.analytic_account_id.id for sub in self]
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "views": [[self.env.ref('analytic.view_account_analytic_line_tree').id, "tree"],
                      [self.env.ref('analytic.view_account_analytic_line_form').id, "form"]],
            "domain": [["account_id", "in", analytic_ids], ['is_timesheet', '=', True]],
            "name": "Contract Timesheets",
        }

    # Action to show tasks for the current subscription
    def action_subscription_tasks(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Tasks",
            "res_model": "project.task",
            "view_mode": 'kanban,tree,form,calendar,pivot,graph',
            "context":{
                'default_group_by': 'stage_id',
                'search_default_project_id': [self.project_id.id],
                'default_project_id': self.project_id.id,
            },
            "search_view_id": self.env.ref('project.view_task_search_form').id,

        }

    # Inherit this method to
    # - remove the generated comment "this invoice covers ..."
    # - add the correct journal
    # - remove the user id (manager of the contract)
    def _prepare_invoice_data(self):
        invoice = super(SaleSubscription, self)._prepare_invoice_data()
        # Comment removal
        if (('comment' in invoice) and ('This invoice covers' in invoice['comment'])):
            invoice['comment'] = ''
        # Set journal
        if self.journal_id and invoice['journal_id'] != self.journal_id:
            invoice['journal_id'] = self.journal_id.id
        # Remove user_id
        if ('user_id' in invoice):
            invoice['user_id'] = False
        return invoice

    def cron_recompute_total_invoice_amount(self):
        subscription_ids = self.env['sale.subscription'].search([('state', 'in', ('open', 'pending')), ('type', '=', 'sale')])
        subscription_ids._compute_total_invoice_amount()
