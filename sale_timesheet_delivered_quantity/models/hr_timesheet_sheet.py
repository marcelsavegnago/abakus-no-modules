from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class HrTimesheetSheet(models.Model):
    _inherit = ['hr_timesheet.sheet']

    @api.multi
    def write(self, vals):
        ret = super(HrTimesheetSheet, self).write(vals)

        if 'state' in vals:

            so_lines = []

            for line in self.timesheet_ids:
                if line.so_line and not line.so_line in so_lines:
                    so_lines.append(line.so_line)

            for so_line in so_lines:
                so_line.sudo()._compute_analytic([('so_line', '=', so_line.id)])

        return ret
