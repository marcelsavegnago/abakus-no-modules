# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = ['project.task']

    partner_phone = fields.Char(string="Partner phone", related='partner_id.phone')
    customer_feedback = fields.Text('Customer Feedback')

    @api.multi
    def set_first_message_as_description(self):
        for task in self:
            if not task.description:
                # get the first message of the issue creator
                messages = task.message_ids.filtered(lambda r: r.author_id == task.partner_id).sorted(key=lambda r: r.date)
                if len(messages) > 0:
                    task.description = messages[0].body

    @api.multi
    def add_partner_as_task_follower(self):
        for task in self:
            if task.partner_id:
                follower_id = False
                for f in task.message_follower_ids:
                    if f.partner_id == task.partner_id:
                        follower_id = f
                        break
                if not follower_id:
                    follower_id = self.env['mail.followers'].create({
                        'res_id': task.id,
                        'res_model': 'project.task',
                        'partner_id': task.partner_id.id,
                    })
                follower_id.write({'subtype_ids':[[4, self.env.ref('mail.mt_comment').id, False]]})
                follower_id.write({'subtype_ids':[[4, self.env.ref('project.mt_task_stage').id, False]]})

    @api.multi
    def match_task_to_project(self):
        generic_email_suffixes = ['gmail.com', 'hotmail.com', 'hotmail.be', 'skyet.be', 'live.com', 'hotmail.fr', 'yahoo.com', 'yahoo.fr']

        for task in self:
            if not task.email_from and not task.partner_id:
                task.message_post(body="No email or partner on this task, impossible to match it automatically on a project")
                continue

            email_match = False
            email_match_email = ''
            email_match_partner_id = None
            is_project_found = False

            project_ids = self.env['project.project'].search([('state', 'in', ('open', 'pending'))])
            # TODO : do the next
            for project in project_ids:
                if project.analytic_account_id.partner_id:
                    # if (project.analytic_account_id.first_subscription_id or (project.analytic_account_id.first_subscription_id and project.analytic_account_id.first_subscription_id.state == 'open')) and project.analytic_account_id.partner_id and 'bl' in project.analytic_account_id.name.lower():
                    project_emails = []
                    for partner in project.analytic_account_id.partner_id.child_ids:
                        if partner.email:
                            project_emails.append([partner.email.lower(), partner.id])
                    if project.analytic_account_id.partner_id.email:
                        project_emails.append([project.analytic_account_id.partner_id.email.lower(), project.analytic_account_id.partner_id.id])

                # Get the suffix of the sender email address
                email_suffix = task.email_from.split("@")[1].lower()
                email_suffix = email_suffix.replace('&#60;', '') # lower than
                email_suffix = email_suffix.replace('&#62;', '') # greater than
                email_simple = task.email_from.lower().replace('&#60;', '').replace('&#62;', '')

                # Try to find the partner using its email from our contacts
                for email in project_emails:
                    if email[0] in task.email_from.lower():
                        email_match = True
                        email_match_email = email[0]
                        email_match_partner_id = email[1]

                # Contact not found, try to match on email suffixes
                if not email_match:
                    for email in project_emails:
                        if (not email_suffix in generic_email_suffixes) and (email[0].find(email_suffix) > 0):
                            email_match = True
                            email_match_email = task.email_from
                            email_match_partner_id = task.partner_id.id

                if email_match:
                    task.write({
                        'project_id' : project.id,
                        'email_from' : email_match_email,
                        'partner_id' : email_match_partner_id,
                        'priority' : '1'
                    })

                    # Print a message in the description
                    if email_match_partner_id == None:
                        task.message_post(body="WARNING ! THIS SENDER HAS NO CONTACT LINKED, CREATE ONE PLEASE\nEMAIL: %s" % (email_match_email))

                    is_project_found = True

                if is_project_found:
                    break
            if not is_project_found:
                task.message_post(body="No project found")


    @api.multi
    def send_confirmation_email_to_customer(self):
        email_template_id = self.env.ref('project_tasks_integration.email_template_task_email_matching_answer')
        if email_template_id:
            email_template_id.sudo().send_mail(self.ids[0], force_send=True)

    @api.multi
    def send_alert_to_team(self):
        email_template_id = self.env.ref('project_tasks_integration.email_template_new_task_email_to_SM')[0]
        for task in self:
            if task.project_id.sale_subscription_id and task.project_id.sale_subscription_id.contract_team:
                email_template_id.sudo().send_mail(self.ids[0], force_send=True, email_values={'partner_ids': [(4, pid.partner_id.id) for pid in task.project_id.sale_subscription_id.contract_team.users]})

