# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class project_service_desk(models.Model):
    _inherit = ['project.project']

    def _get_default_project_type(self):
        context = self.env.context
        if context is None:
            context = {}
        if 'default_project_type' in context:
            if context['default_project_type']:
                return context['default_project_type']
        return False

    state = fields.Selection([('draft','New'),
                                   ('open','In Progress'),
                                   ('cancelled', 'Cancelled'),
                                   ('pending','Pending'),
                                   ('close','Closed')],
                                  'Status', required=True, copy=False, default='open')
    project_type = fields.Selection([('support', 'Support'), ('installation', 'Installation'), ('internal', 'Internal'), ('development', 'Development'), ('other', 'Other')], 'Type of Project', default=_get_default_project_type)
    calendar_event_ids = fields.One2many('calendar.event', 'project_id', string="Events")
    calendar_event_count = fields.Integer(string="Event count", compute='_computeeventcount')

    @api.multi
    @api.depends('calendar_event_ids')
    def _computeeventcount(self):
        for project in self:
            project.calendar_event_count = len(project.calendar_event_ids)

