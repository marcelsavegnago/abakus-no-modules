# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

class contract_report(models.Model):
    _name = 'contract.report'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End date")
    statistics = fields.Boolean(string="Statistics")
    remove_prices = fields.Boolean(string="Remove prices")
    only_worklogs = fields.Boolean(string="Only worklogs")
    group_by_issue_and_task = fields.Boolean(string="Group by Issue/Task", default=True)

    @api.model
    def get_instance(self):
        return self.search([('id','=',1)], limit=1)

    @api.model
    def get_start_date(self):
        contract_report = self.get_instance()
        if contract_report and contract_report.start_date:
            return contract_report.start_date
        return False

    @api.model
    def get_end_date(self):
        contract_report = self.get_instance()
        if contract_report and contract_report.end_date:
            return contract_report.end_date
        today = datetime.today()
        first = datetime(today.year, today.month, 1)
        return first + timedelta(days=-1)

    @api.model
    def get_statistics(self):
        contract_report = self.get_instance()
        if contract_report:
            return contract_report.statistics
        return False
        
    @api.model
    def get_remove_prices(self):
        contract_report = self.get_instance()
        if contract_report:
            return contract_report.remove_prices
        return False

    @api.model
    def get_only_worklogs(self):
        contract_report = self.get_instance()
        if contract_report:
            return contract_report.only_worklogs
        return False

    @api.model
    def get_group_by_issue_and_task(self):
        contract_report = self.get_instance()
        if contract_report:
            return contract_report.group_by_issue_and_task
        return False
    
class contract_report_wizard(models.TransientModel):
    _name = 'contract.report.wizard'

    def _default_start_date(self):
        return self.env['contract.report'].get_start_date()

    def _default_end_date(self):
        return self.env['contract.report'].get_end_date()
    
    def _default_statistics(self):
        return self.env['contract.report'].get_statistics()
    
    def _default_remove_prices(self):
        return self.env['contract.report'].get_remove_prices()

    def _default_only_worklogs(self):
        return self.env['contract.report'].get_only_worklogs()

    def _default_group_by_issue_and_task(self):
        return self.env['contract.report'].get_group_by_issue_and_task()
    
    start_date = fields.Date(string="Start date", default=_default_start_date)
    end_date = fields.Date(string="End date", default=_default_end_date)
    statistics = fields.Boolean(string="Statistics", default=_default_statistics)
    remove_prices = fields.Boolean(string="Remove prices", default=_default_remove_prices)
    only_worklogs = fields.Boolean(string="Only worklogs", default=_default_only_worklogs)
    group_by_issue_and_task = fields.Boolean(string="Group by Issue/Task", default=_default_group_by_issue_and_task)
    
    @api.multi
    def save(self):
        self.ensure_one()
        self.env['contract.report'].browse(1).write({
            'end_date' : self.end_date,
            'statistics' : self.statistics,
            'remove_prices':self.remove_prices,
            'only_worklogs': self.only_worklogs,
            'group_by_issue_and_task': self.group_by_issue_and_task
        })                                            
        return {}

    @api.model
    def reset_stats(self):
        pass

    #get context from method print_timesheets_report in sale.subscription (contract_report)
    @api.multi
    def print_report(self):
        self.save()

        account_ids = self.env.context['account_ids']
        return self.env.ref('contract_report.contract_abakus').report_action(account_ids)
        
    #get context from method action_service_report_sent in sale.subscription (contract_report)
    @api.multi
    def send_by_email(self):    
        self.save()
        compose_form_id = self.env.context['compose_form_id']
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': self.env.context,
        }