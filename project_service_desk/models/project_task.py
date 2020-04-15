# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)

class project_task_service_desk(models.Model):
    _inherit = ['project.task']

    project_type = fields.Selection(related='project_id.project_type', string='Project Type', store=True)

    def _get_default_project_id(self):
        project_id = False
        context = self.env.context
        if context is None:
            context = {}
        if 'default_analytic_account_id' in context:
            analytic_account = self.env['account.analytic.account'].browse(context['default_analytic_account_id'])
            if analytic_account and len(analytic_account.project_ids) > 0:
                project_id = analytic_account.project_ids[0]
            if analytic_account and len(analytic_account.subscription_ids) > 0:
                if analytic_account.subscription_ids[0].project_id:
                    project_id = analytic_account.subscription_ids[0].project_id
        if project_id != False:
            return project_id.id
        return False

    def _get_default_stage_id(self):
        project_id = False
        context = self.env.context
        if context is None:
            context = {}
        default_project_id = context.get('default_project_id')
        if default_project_id:
            return self.stage_find(default_project_id, [('fold', '=', False)])
        if 'default_analytic_account_id' in context:
            analytic_account = self.env['account.analytic.account'].browse(context['default_analytic_account_id'])
            if analytic_account and len(analytic_account.project_ids) > 0:
                project_id = analytic_account.project_ids[0]
            if analytic_account and len(analytic_account.subscription_ids) > 0:
                if analytic_account.subscription_ids[0].project_id:
                    project_id = analytic_account.subscription_ids[0].project_id
        if project_id != False:
            return self.stage_find(default_project_id, [('fold', '=', False)])
        return False

    def _get_default_partner(self):
        context = self.env.context
        project_id = False
        if context is None:
            context = {}
        if 'default_project_id' in context:
            project = self.env['project.project'].browse(context['default_project_id'])
            if project and project.partner_id:
                return project.partner_id.id
        if 'default_analytic_account_id' in context:
            analytic_account = self.env['account.analytic.account'].browse(context['default_analytic_account_id'])
            if analytic_account and len(analytic_account.project_ids) > 0:
                project_id = analytic_account.project_ids[0]
            if analytic_account and len(analytic_account.subscription_ids) > 0:
                if analytic_account.subscription_ids[0].project_id:
                    project_id = analytic_account.subscription_ids[0].project_id
        if project_id != False:
            return project_id.partner_id.id
        return False

    _defaults = {
        'project_id': lambda s: s._get_default_project_id(),
        'stage_id': lambda s: s._get_default_stage_id(),
        'partner_id': lambda s: s._get_default_partner(),
    }
