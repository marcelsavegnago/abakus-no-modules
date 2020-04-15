# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class Bonus(models.Model):
    _name = 'hr.bonus'
    _order = 'date desc'

    name = fields.Char(copy=False, index=True, required=True, readonly=True,
                       states={'draft': [('readonly', False)]})
    description = fields.Text(readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], default='draft', required=True)
    date = fields.Datetime(required=True, readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env['hr.employee'].search(
                                      [('user_id', '=', self.env.user.id)]))

    @api.one
    def action_draft(self):
        self.write({'state': 'draft'})

    @api.one
    def action_submit(self):
        self.write({'state': 'submitted'})

    @api.one
    def action_approve(self):
        self.write({'state': 'approved'})

    @api.one
    def action_refuse(self):
        self.write({'state': 'refused'})

    @api.one
    def action_unlink(self):
        self.sudo().unlink()
