# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    planned_hours = fields.Float(string='Initial Planned Hours')

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        domain = super(SaleOrderLine, self).product_id_change()

        if self.product_id.type == 'service' and self.product_id.track_service == 'task':
            self.planned_hours = self.product_id.planned_hours

        return domain

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        data = super(SaleOrderLine, self).product_uom_change()

        if self.product_id.type == 'service' and self.product_id.track_service == 'task':
            self.planned_hours = self.product_id.planned_hours * self.product_uom_qty

        return data

    def _timesheet_create_task(self, project):
        """ Generate task for the given so line, and link it.
            :param project: record of project.project in which the task should be created
            :return task: record of the created task
        """
        project.name = (self.order_id.partner_id.ref if self.order_id.partner_id.ref else self.order_id.partner_id.name) + " - " + self.order_id.name
        project.project_type = 'installation'

        project_stage_ids = self.env['project.task.type'].search([
            '|', ('name', '=ilike', 'New'),
            '|', ('name', '=ilike', 'Open'), ('name', '=ilike', 'Done')])
        project.type_ids = project_stage_ids

        values = self._timesheet_create_task_prepare_values(project)
        values['remaining_hours'] = self.planned_hours
        values['planned_hours'] = self.planned_hours
        values['name'] = '%s - %s (%s)' % (self.name, self.sale_line_id.order_id.name, self.origin or '')
        values['date_deadline'] = self.scheduled_date
        values['description'] = '%s<br />%s' % (self.product_id.name, self.name)
        values['stage_id'] = project.type_ids[0].id
        task = self.env['project.task'].sudo().create(values)
        self.write({'task_id': task.id})
        # post message on task
        task_msg = _("This task has been created from: <a href=# data-oe-model=sale.order data-oe-id=%d>%s</a> (%s)") % (self.order_id.id, self.order_id.name, self.product_id.name)
        task.message_post(body=task_msg)
        return task