# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class project_service_desk(models.Model):
    _inherit = ['project.project']

    state = fields.Selection([('draft','New'),
                                   ('open','In Progress'),
                                   ('cancelled', 'Cancelled'),
                                   ('pending','Pending'),
                                   ('close','Closed')],
                                  'Status', required=True, copy=False, default='open')
    project_type = fields.Selection([('support', 'Support'), ('installation', 'Installation'), ('internal', 'Internal'), ('development', 'Development'), ('other', 'Other')], 'Type of Project')
    calendar_event_ids = fields.One2many('calendar.event', 'project_id', string="Events")
    calendar_event_count = fields.Integer(string="Event count", compute='_computeeventcount')

    defaults = {
        'project_type ': lambda self, cr, uid, ctx=None: self._get_default_project_type(cr, uid, context=ctx)
    }

    def _get_default_project_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        if 'default_project_type' in context:
            if context['default_project_type']:
                return context['default_project_type']    
        return False

    @api.multi
    @api.depends('calendar_event_ids')
    def _computeeventcount(self):
        for project in self:
            project.calendar_event_count = len(project.calendar_event_ids)

