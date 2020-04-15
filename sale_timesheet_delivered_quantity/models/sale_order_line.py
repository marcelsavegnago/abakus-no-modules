from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    @api.multi
    def _compute_analytic(self, domain=None):
        lines = {}
        if not domain:
            # To filter on analyic lines linked to an expense
            expense_type_id = self.env.ref('account.data_account_type_expenses', raise_if_not_found=False)
            expense_type_id = expense_type_id and expense_type_id.id
            domain = [
                ('so_line', 'in', self.ids),
                '|',
                    ('amount', '<', 0),
                    '&',
                        ('amount', '=', 0),
                        '|',
                            ('move_id', '=', False),
                            ('move_id.account_id.user_type_id', '=', expense_type_id)
            ]

        data = self.env['account.analytic.line'].read_group(
            domain,
            ['so_line', 'unit_amount', 'product_uom_id', 'sheet_id'], ['product_uom_id', 'so_line', 'sheet_id'], lazy=False
        )
        # If the unlinked analytic line was the last one on the SO line, the qty was not updated.
        force_so_lines = self.env.context.get("force_so_lines")
        if force_so_lines:
            for line in force_so_lines:
                lines.setdefault(line, 0.0)
        for d in data:
            if not d['product_uom_id']:
                continue

            line = self.browse(d['so_line'][0])
            lines.setdefault(line, 0.0)

            sheet = self.env['hr_timesheet.sheet'].browse(d['sheet_id'][0]) if d['sheet_id'] else False

            if sheet and sheet.state == 'done':
                uom = self.env['product.uom'].browse(d['product_uom_id'][0])
                if line.product_uom.category_id == uom.category_id:
                    qty = self.env['product.uom']._compute_qty_obj(uom, d['unit_amount'], line.product_uom)
                else:
                    qty = d['unit_amount']
                lines[line] += qty

        for line, qty in lines.items():
            line.qty_delivered = qty
        return True