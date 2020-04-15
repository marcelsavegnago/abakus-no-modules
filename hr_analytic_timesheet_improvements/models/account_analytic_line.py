# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools.translate import _
from odoo.exceptions import UserError
import html2text


import logging
_logger = logging.getLogger(__name__)

class AnalyticAccountLine(models.Model):
    _inherit = 'account.analytic.line'

    """_defaults = {
        'is_timesheet ': lambda self, cr, uid, ctx=None: self._get_is_timesheet(cr, uid, context=ctx)
    }

    def _get_is_timesheet(self, cr, uid, context=None):
        if context is None:
            context = {}
        if 'default_is_timesheet' in context:
            if context['default_carrier_id']:
                return True    
        return False
        """

    def _get_default_date(self):
        return datetime.strftime(self.check_and_correct_date_in_fifteen_step(datetime.now()), '%Y-%m-%d %H:%M:%S')

    date_begin = fields.Datetime(string='Start Datetime', default=_get_default_date)
    flat_name = fields.Char(string="Display Name")
    task_state = fields.Many2one(related='task_id.stage_id', string="Task State")
    project_id = fields.Many2one('project.project', string="Project", default=lambda self: self._get_default_project())
    task_planned_hours = fields.Float(string="Planned time on task", related='task_id.planned_hours')

    @api.multi
    @api.onchange('name')
    def compute_display_name(self):
        for line in self:
            if line.name:
                line.flat_name = html2text.html2text(line.name)

    @api.multi
    @api.onchange('flat_name')
    def compute_name(self):
        for line in self:
            if line.flat_name:
                line.name = line.flat_name

    def _get_default_project(self):
        if self.account_id:
            if len(self.account_id.project_ids) > 0:
                if self.account_id.project_ids[0] and self.account_id.project_ids[0].id:
                    return self.account_id.project_ids[0].id
        return False
    
    def check_and_correct_date_in_fifteen_step(self, date):
        newdate = date
        newhour = newdate.hour
        step = 0
        round = False
        minute_under_fifteen = newdate.minute
        while (minute_under_fifteen > 15):
           minute_under_fifteen = minute_under_fifteen - 15
           step+=1
        if(minute_under_fifteen>=(15/2)):
            round = True
        if round:
            newminute = (step*15)+15
            if newminute==60:
                newdate = newdate + timedelta(hours=1)
                newminute = 0
        else:
            newminute = step*15
        
        newdate = newdate.replace(minute=newminute, second=0)
        return newdate

    # set the date of date_begin to "date" to avoid inconsistency problems
    @api.multi
    @api.onchange('date_begin')
    def copy_dates(self):
        self.date = self.date_begin

    @api.multi
    def remove_quarter(self):
        for line in self:
            if line.unit_amount > 0:
                line.unit_amount = line.unit_amount - 0.25

    @api.multi
    def add_quarter(self):
        for line in self:
            line.unit_amount = line.unit_amount + 0.25

    @api.multi
    def write(self, vals):
        self._check_rights_to_write()
        newdate = False
        if vals.get('date_begin'):
            start_date = datetime.strptime(vals.get('date_begin'), '%Y-%m-%d %H:%M:%S')
            newdate = self.check_and_correct_date_in_fifteen_step(start_date)
            if start_date.minute != newdate.minute or start_date.second != newdate.second:
                vals.update({'date_begin': datetime.strftime(newdate, '%Y-%m-%d %H:%M:%S')})
            vals.update({'date': newdate.date()})
        
        result = super(AnalyticAccountLine, self).write(vals)
        return result

    @api.model
    def create(self, vals):
        # Test if timesheet or not
        if vals.get('is_timesheet'):
            if vals.get('date_begin'):
                start_date = datetime.strptime(vals.get('date_begin'), '%Y-%m-%d %H:%M:%S')
                newdate = self.check_and_correct_date_in_fifteen_step(start_date)
                if start_date.minute != newdate.minute or start_date.second != newdate.second:
                    start_date = self.check_and_correct_date_in_fifteen_step(start_date)
                    vals.update({'date_begin': datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')})
                    vals.update({'date': newdate.date()})
            elif vals.get('date'):
                date = datetime.strptime(vals.get('date'), '%Y-%m-%d')
                date = self.check_and_correct_date_in_fifteen_step(date)
                vals.update({'date': date.date()})
                vals.update({'date_begin': datetime.strftime(date, '%Y-%m-%d %H:%M:%S')})
            else:
                date = self.check_and_correct_date_in_fifteen_step(datetime.now())
                vals.update({'date_begin': datetime.strftime(date, '%Y-%m-%d %H:%M:%S')})
                vals.update({'date': datetime.strftime(date, '%Y-%m-%d')})

        hr_analytic_timesheet_id = super(AnalyticAccountLine, self).create(vals)
        return hr_analytic_timesheet_id

    @api.multi
    def unlink(self):
        self._check_rights_to_write()
        return super(AnalyticAccountLine, self).unlink()


    # The following method is called when writing on the AAL
    # I will inherit it to allow the HR Manager & Account Manager
    # to edit them even if the Timesheet is confirmed
    def _check_rights_to_write(self):
        f1 = self.env.user.has_group('base.group_hr_user')
        f2 = self.env.user.has_group('account.group_account_manager')
        if not (f1 or f2):
            for line in self:
                if line.validated: #TODO check if OK
                    raise UserError(_('You cannot modify an entry in a confirmed timesheet. Only HR Officer and Account Manager can do it.'))
        return True


    @api.multi
    @api.onchange('project_id')
    def set_correct_analytic_account(self):
        for line in self:
            if line.project_id:
                line.account_id = line.project_id.analytic_account_id

    @api.model
    def create(self, vals):
        if 'project_id' not in vals:
            project_id = self.env['project.project'].search([('analytic_account_id', '=', vals['account_id'])])
            if project_id:
                vals.update({'project_id': project_id.id})
        rec = super(AnalyticAccountLine, self).create(vals)
        return rec

    @api.multi
    def close_task_issue(self):
        self.ensure_one()
        if self.task_id:
            self.task_id.action_close()

    @api.multi
    def delete_worklog(self):
        self.unlink()
