from odoo import models, fields, api
from datetime import datetime
import logging


_logger = logging.getLogger(__name__)

class expense_with_social_banner(models.Model):
    _inherit = ['hr.expense']

    banner_text = fields.Html(string="Important Message", default=lambda self: self._get_default_banner())

    @api.model
    def _get_default_banner(self):
        return self._get_banner()

    @api.multi
    def _compute_banner_text(self):
        for expense in self:
            expense = self._get_banner()

    def _get_banner(self):
        # search for banners that are online
        banners = self.env['social.banner'].search([('state', '=', 'confirm')])

        text = ""
        for banner in banners:
            # search for banners that are visible on this form
            if banner.visible_on != 'all' and banner.visible_on != 'holiday':
                continue
            # search for banners that are set to be visible from
            if banner.valid_from:
                if datetime.strftime(datetime.now(), '%Y-%m-%d') < banner.valid_from:
                    continue
            # search for banners that are set to be visible to
            if banner.valid_to:
                if banner.valid_to < datetime.strftime(datetime.now(), '%Y-%m-%d'):
                    continue
            # search for banners that are visible for this employee (department / company)
            if banner.visible_for != 'all':
                # boolean selector
                concerned = False
                # get employee
                employee = None
                user = self.env['res.users'].browse(self.env.uid)
                if len(user.employee_ids) > 1:
                    employee = user.employee_ids[0]
                # by department
                if banner.visible_for == 'department':
                    for department in banner.department_ids:
                        if user.employee_ids[0] in department.member_ids:
                            concerned = True
                # by company
                if banner.visible_for == 'company':
                    for company in banner.company_ids:
                        if user.employee_ids[0].company_id == company:
                            concerned = True
                if not concerned:
                    continue

            text += banner.banner_representation

            # Create a red entry
            read = self.env['social.banner.read'].search([('banner_id', '=', banner.id), ('user_id', '=', self.env.uid)])
            if len(read) < 1:
                self.env['social.banner.read'].create({
                        'banner_id': banner.id,
                        'user_id': self.env.uid,
                        'date': datetime.now(),
                    }
                )
        return text
