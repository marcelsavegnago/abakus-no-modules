# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
import logging
_logger = logging.getLogger(__name__)

class ProjectProject(models.Model):
    _inherit = ['project.project']

    default_task_master_type_id = fields.Many2one('project.task.mastertype', string="Default Task Type")
