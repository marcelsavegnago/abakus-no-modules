# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import append_content_to_html

import base64
import logging
_logger = logging.getLogger(__name__)


class AccountFollowUpReport(models.AbstractModel):
    _inherit = 'account.followup.report'

    @api.model
    def send_email(self, options):
        if options and "partner_id" in options:
            partner_id = self.env['res.partner'].browse(options.get('partner_id'))
            email = self.env['res.partner'].browse(partner_id.address_get(['invoice'])['invoice']).email
            if email and email.strip():
                # Get report lines, containing invoice number
                lines = self.env['account.followup.report'].with_context(lang=partner_id.lang, public=True).get_lines(options)
                ids = []
                for line in lines:
                    if line['name'] == '':
                        continue
                    if line['action'][1]:
                        ids.append(line['action'][1])

                #Get all invoices related to numbers then browse it.
                invoices = self.env['account.invoice'].search([('id', 'in', ids)])
                for invoice in invoices:
                    # Create ir.attachment and PDF for invoice when it doesn't exists
                    pdf = self.env.ref('account.account_invoices').sudo().render_qweb_pdf([invoice.id])[0]
                attachments = self.env['ir.attachment'].search([('res_id', 'in', invoices.mapped('id')), ('res_model', '=', "account.invoice")]).mapped('id')

                # Attach to all related PDF to email
                email = self.env['mail.mail'].create({
                    'subject': _('%s Payment Reminder') % self.env.user.company_id.name,
                    'body_html': append_content_to_html(self.with_context(public=True, mode='print').get_html(options),
                                                        self.env.user.signature, plaintext=False),
                    'email_from': self.env.user.email or '',
                    'email_to': email,
                    'attachment_ids': [(6, 0, attachments)]
                })
                msg = _(': Sent a followup email')
                partner_id.message_post(body=msg, subtype='account_reports.followup_logged_action')
                return True
        return False
