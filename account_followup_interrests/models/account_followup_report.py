# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, tools, _
from datetime import datetime
from hashlib import md5
from odoo.tools.misc import formatLang
import time
from odoo.tools.safe_eval import safe_eval
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
import math

import logging
_logger = logging.getLogger(__name__)


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    @api.model
    def get_lines(self, context_id, line_id=False, public=False):
        if not public and "public" in self.env.context:
            public = self.env.context.get('public')
        # Get date format for the lang
        partner_id = self.env['res.partner'].browse(context_id.get('partner_id'))
        lang_code = partner_id.lang or self.env.user.lang or 'en_US'
        lang_ids = self.env['res.lang'].search([('code', '=', lang_code)], limit=1)
        date_format = lang_ids.date_format or DEFAULT_SERVER_DATE_FORMAT

        def formatLangDate(date):
            date_dt = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
            return date_dt.strftime(date_format)

        lines = []
        res = {}
        today = datetime.today().strftime('%Y-%m-%d')
        line_num = 0
        for l in partner_id.unreconciled_aml_ids:
            if public and l.blocked:
                continue
            amount = l.currency_id and l.amount_residual_currency or l.amount_residual
            currency = l.currency_id or l.company_id.currency_id
            if currency not in res:
                res[currency] = []
            res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            total_interest = 0
            total_allowance = 0
            total_all = 0
            aml_recs = sorted(aml_recs, key=lambda aml: aml.blocked)
            for aml in aml_recs:
                amount = aml.currency_id and aml.amount_residual_currency or aml.amount_residual
                date_due = formatLangDate(aml.date_maturity or aml.date)
                total += not aml.blocked and amount or 0
                total_interest += not aml.blocked and aml.payments_interests or 0
                total_allowance += not aml.blocked and aml.payments_allowances or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_payment:
                    date_due = ''

                late_days = 0
                allowances = formatLang(self.env, 0, currency_obj=currency)
                interests = formatLang(self.env, 0, currency_obj=currency)
                total_due = formatLang(self.env, float(amount), currency_obj=currency)
                if amount > 0:
                    late_days = aml.late_days > 0 and aml.late_days or 0
                    allowances = formatLang(self.env, aml.payments_allowances, currency_obj=currency)
                    interests = formatLang(self.env, aml.payments_interests, currency_obj=currency)
                    total_due = formatLang(self.env, float(amount + aml.payments_interests + aml.payments_allowances), currency_obj=currency)
                amount = formatLang(self.env, amount, currency_obj=currency)
                
                line_num += 1
                columns = [
                        {'name': formatLangDate(aml.date)},
                        {'name': late_days},
                        {'name': amount},
                        {'name': allowances},
                        {'name': interests},
                        {'name': total_due},
                    ]
                if is_overdue:
                    columns.insert(1,{'name': date_due, 'style': 'color:red'})
                else:
                    columns.insert(1,{'name': date_due})
                if not public:
                    columns.insert(2, {'name': aml.expected_pay_date and aml.expected_pay_date or ''})
                lines.append({
                    'id': aml.id,
                    'name': aml.move_id.name,
                    'action': aml.get_model_id_and_name(),
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'footnotes': {},
                    'unfoldable': False,
                    'columns': columns,
                    'blocked': aml.blocked,
                })
            total_all = total_issued + total_interest + total_allowance
            total_str = formatLang(self.env, total, currency_obj=currency)
            base_columns = []
            for i in range(0, 5 if public else 6):
                base_columns.append({'name': ''})
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'type': 'total',
                'footnotes': {},
                'unfoldable': False,
                'level': 0,
                'columns': base_columns + [{'name': total >= 0 and _('Total Due') or ''}, {'name': total_str}],
                'class': 'total',
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'type': 'total',
                    'footnotes': {},
                    'unfoldable': False,
                    'level': 0,
                    'columns': base_columns + [{'name': total >= 0 and _('Total Overdue') or ''}, {'name': total_issued}],
                    'class': 'total',
                })
            if total_interest > 0:
                total_interest = formatLang(self.env, total_interest, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'type': 'total',
                    'footnotes': {},
                    'unfoldable': False,
                    'level': 0,
                    'columns': base_columns + [{'name': total >= 0 and _('Interests Total') or ''}, {'name': total_interest}],
                    'class': 'total',
                })
            if total_allowance > 0:
                total_allowance = formatLang(self.env, total_allowance, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'type': 'total',
                    'footnotes': {},
                    'unfoldable': False,
                    'level': 0,
                    'columns': base_columns + [{'name': total >= 0 and _('Allowance Total') or ''}, {'name': total_allowance}],
                    'class': 'total',
                })
            total_all = formatLang(self.env, total_all, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'type': 'total',
                'footnotes': {},
                'unfoldable': False,
                'level': 0,
                'columns': base_columns + [{'name': total >= 0 and _('Total') or ''}, {'name': total_all}],
                'class': 'total',
            })
        return lines


    def get_columns_name(self, options):
        if self.env.context.get('public'):
            return [
                {'name': _("Invoice"), 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Due Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Overdue days'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Amount'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Allowances'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Interests'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Total Due'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
            ]
        return [
                {'name': _("Invoice"), 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Due Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Expected Date'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Overdue days'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Amount'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Allowances'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Interests'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
                {'name': _('Total Due'), 'class': 'number', 'style': 'text-align:center; white-space:nowrap;'},
            ]

# class account_report_context_followup(models.TransientModel):
#     _inherit = "account.report.context.followup"
#
#
#     @api.multi
#     def get_columns_types(self):
#         if self.env.context.get('public'):
#             return ['date', 'date', 'number', 'number', 'number', 'number', 'number']
#         return ['date', 'date', 'number', 'date', 'checkbox', 'number', 'number', 'number', 'number']
