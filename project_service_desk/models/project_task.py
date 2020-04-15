# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


import logging
_logger = logging.getLogger(__name__)

class project_task_service_desk(models.Model):
    _inherit = ['project.task']

    project_type = fields.Selection(related='project_id.project_type', string='Project Type', store=True)

    def _get_default_project_id(self, cr, uid, context=None):
        project_id = False
        if context is None:
            context = {}
        if 'default_analytic_account_id' in context:
            analytic_account = self.pool.get('account.analytic.account').browse(cr, uid, context['default_analytic_account_id'], context=context)
            if analytic_account and len(analytic_account.project_ids) > 0:
                project_id = analytic_account.project_ids[0]
            if analytic_account and len(analytic_account.subscription_ids) > 0:
                if analytic_account.subscription_ids[0].project_id:
                    project_id = analytic_account.subscription_ids[0].project_id
        if project_id != False:
            return project_id.id
        return False

    def _get_default_stage_id(self, cr, uid, context=None):
        project_id = False
        if context is None:
            context = {}
        default_project_id = context.get('default_project_id')
        if default_project_id:
            return self.stage_find(cr, uid, [], default_project_id, [('fold', '=', False)], context=context)
        if 'default_analytic_account_id' in context:
            analytic_account = self.pool.get('account.analytic.account').browse(cr, uid, context['default_analytic_account_id'], context=context)
            if analytic_account and len(analytic_account.project_ids) > 0:
                project_id = analytic_account.project_ids[0]
            if analytic_account and len(analytic_account.subscription_ids) > 0:
                if analytic_account.subscription_ids[0].project_id:
                    project_id = analytic_account.subscription_ids[0].project_id
        if project_id != False:
            return self.stage_find(cr, uid, [], default_project_id, [('fold', '=', False)], context=context)
        return False

    def _get_default_partner(self, cr, uid, context=None):
        project_id = False
        if context is None:
            context = {}
        if 'default_project_id' in context:
            project = self.pool.get('project.project').browse(cr, uid, context['default_project_id'], context=context)
            if project and project.partner_id:
                return project.partner_id.id
        if 'default_analytic_account_id' in context:
            analytic_account = self.pool.get('account.analytic.account').browse(cr, uid, context['default_analytic_account_id'], context=context)
            if analytic_account and len(analytic_account.project_ids) > 0:
                project_id = analytic_account.project_ids[0]
            if analytic_account and len(analytic_account.subscription_ids) > 0:
                if analytic_account.subscription_ids[0].project_id:
                    project_id = analytic_account.subscription_ids[0].project_id
        if project_id != False:
            return project_id.partner_id.id
        return False

    _defaults = {
        'project_id': lambda s, cr, uid, c: s._get_default_project_id(cr, uid, context=c),
        'stage_id': lambda s, cr, uid, c: s._get_default_stage_id(cr, uid, context=c),
        'partner_id': lambda s, cr, uid, c: s._get_default_partner(cr, uid, context=c),
    }
