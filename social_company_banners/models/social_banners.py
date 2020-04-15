from odoo import models, fields, api
import logging


_logger = logging.getLogger(__name__)

class social_banner(models.Model):
    _name = 'social.banner'

    name = fields.Char(string="Title", required=True)
    text = fields.Html(string="Text")
    state = fields.Selection([('new', 'New'), ('confirm', 'Published'), ('done', 'Ended')], default='new', string="State")
    valid_from = fields.Date(string="Visible from")
    valid_to = fields.Date(string="Visible till")
    priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], name="Priority", default="medium", required=True)
    visible_on = fields.Selection([('all', 'All places'), ('timesheet', 'Timesheet form'), ('holiday', 'Holidays form'), ('expense', 'Expenses form')], default='all', string="Visible on", required=True)
    visible_for = fields.Selection([('all', 'All employees'), ('department', 'Specified Departments'), ('company', 'Specified Companies')], default='all', string="Visible for", required=True)
    department_ids = fields.Many2many('hr.department', string="Selected Departments")
    company_ids = fields.Many2many('res.company', string="Selected companies")
    read_by_ids = fields.One2many('social.banner.read', 'banner_id', string="Read by")
    banner_representation = fields.Html(compute='_compute_banner_representation')

    @api.multi
    def _compute_banner_representation(self):
        for banner in self:
            representation = ''
            if banner.priority == 'low':
                representation += "<h2 style='color: green;'>" + banner.name + "</h2>"
            if banner.priority == 'medium':
                representation += "<h2 style='color: orange;'>" + banner.name + "</h2>"
            if banner.priority == 'high':
                representation += "<h2 style='color: red; font-weight: bold;'>" + banner.name + "</h2>"
            representation += banner.text + '<br />'
            banner.banner_representation = representation

    @api.multi
    def action_confirm(self):
        for banner in self:
            banner.state = 'confirm'

    @api.multi
    def action_stop(self):
        for banner in self:
            banner.state = 'done'

    @api.multi
    def action_renew(self):
        for banner in self:
            banner.state = 'new'
