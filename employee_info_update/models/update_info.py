from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class UpdateInfo(models.Model):
    _name = "update.info"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Employee Info Update"
    _rec_name = 'name'
    
    def get_default_approval_flow(self):
        return self.env['approval.flow'].search([('model_apply', '=', 'employee_info_update'), ('company_id', '=', self.env.company.id)], limit=1)

    
    employee_id = fields.Many2one('hr.employee', string='Employee Name', index=True, ondelete="restrict", tracking=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department')
    update_date = fields.Date(string='Update Date')
    update_detail = fields.One2many('detail.update', inverse_name='update_id', string='Update Detail', required=True)
    
    reason = fields.Text(string='Reason', required=True)
    name = fields.Char(string='Name')

    # workflow setup

    status = fields.Selection([
        ('draft', 'Draft'),
        ('to_submit', 'Submit'),
        ('submitted', 'To Approve'),
        ('reject', 'Rejected'),
        ('approved', 'Approved')
    ], string="Status", default="draft", required=True, readonly=True, tracking=True)

    is_invisible_button = fields.Boolean(string="Is Invisible Button", compute="_compute_invisible_button")
    is_approver = fields.Boolean(string="Is Approver", compute="_compute_is_approver_refuse")

    current_user_id = fields.Char(string="Current User", readonly=True, store=True)
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user)

    current_user_in_stage_ids = fields.Many2many("res.users", string="Current User in Stage", default=lambda self: self.current_stage_id.user_ids.ids)
    stage_id = fields.Many2one("movement.stage", string="Stage", compute='_compute_stage_id',
                               groups="advanced_movement.group_manager")
    current_stage_id = fields.Many2one('movement.stage', string='Current Stage',
                                       groups="advanced_movement.group_user")

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    employee_info_id = fields.Many2one("approval.flow", string="Employee Info Update", change_default=True, default=get_default_approval_flow)


    @api.model
    def default_get(self, fields):
        res = super(UpdateInfo, self).default_get(fields)
        # Get the current user and set the name in current_user_id
        current_user = self.env.user
        res['current_user_id'] = current_user.name
        return res
    
    @api.model
    def write(self, vals):
        # Update the current user field when saving the record
        vals['current_user_id'] = self.env.user.name
        return super(UpdateInfo, self).write(vals)
    
    
    @api.model
    def create(self, vals):
        record = super(UpdateInfo, self).create(vals)
        _logger.info('This is a comment log')
        record.name = f'UI {record.id}'
        return record
        
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.company_id = self.employee_id.company_id
            self.department_id = self.employee_id.department_id
            
    #Update employee table data when triggered
    def action_confirm(self):
        vals = {'status': 'approved'}
        employee_vals = {}
        for detail in self.update_detail:
            employee_vals.update({detail.field_id.name: detail.new_value})
        self.write(vals)
        self.employee_id.write(employee_vals)
        
        
   # Workflow Setup

    @api.depends('status', 'current_stage_id.user_ids')
    def _compute_is_approver_refuse(self):
        for rec in self:
            all_stages = self.env['movement.stage'].search([('approval_flow_id', '=', rec.employee_info_id.id)])
            user = rec.env.user
            if rec.employee_info_id.sequenced:
                rec.current_user_in_stage_ids = rec.current_stage_id.user_ids
                
            elif rec.employee_info_id.parallel:
                rec.current_user_in_stage_ids = rec.employee_info_id.stage_id.user_ids

            if rec.status == 'submitted' and user in all_stages.user_ids:
                rec.is_approver = False
            else:
                rec.is_approver = True

    def action_confirm_movement(self):
        for rec in self:
            all_stages = self.env['movement.stage'].search(
                [('approval_flow_id', '=', rec.employee_info_id.id), ('company_id', '=', rec.company_id.id)])
            # all_movement_emp = self.sudo().search(
            #     [('s_employee_id', '=', rec.s_employee_id)], order='create_date desc').filtered(lambda self: self.status != 'reject')
            # if len(all_movement_emp) > 1:
            #     selection_name = rec.get_selection_name(all_movement_emp[0].status)
            #     raise UserError(_("Employee already has a movement request which overlaps with this effective date: In %s - %s", all_movement_emp[0].effective_date, selection_name))
            if not rec.employee_info_id.stage_id:
                raise UserError(_("Approval Flow not setting ,please setting before create record."))

            if rec.status != 'draft':
                raise UserError(_("You can not approve while its status is not Draft."))
        if rec.employee_info_id.sequenced:
            rec.current_user_in_stage_ids = rec.current_stage_id.user_ids.ids
            self.write({'status': 'submitted', 'current_stage_id': all_stages[0].id})
        else:
            rec.current_user_in_stage_ids = rec.employee_info_id.stage_id.user_ids.ids
            self.write({'status': 'submitted'})
            for rec in all_stages:
                rec.write({'status': 'pending'})
        return True

    def action_approved_movement(self):
        for rec in self:
            rec.current_user_in_stage_ids = rec.current_stage_id.user_ids.ids
            user = rec.env.user
            all_stages = self.env['movement.stage'].search([('approval_flow_id', '=', rec.employee_info_id.id)])
            if rec.status == 'approved':
                raise UserError(_("This movement has already been approved."))
            if rec.status == 'reject':
                raise UserError(_("You cannot approve a request which is in Rejected state."))
            if rec.employee_info_id.parallel:
                all_stages = self.env['movement.stage'].search(
                    [('approval_flow_id', '=', rec.employee_info_id.id)])
                user = rec.env.user
                current_actions_stages = all_stages.filtered(lambda rec: rec.status != 'approved')
                if user in current_actions_stages.user_ids:
                    for stage in current_actions_stages:
                        if user in stage.user_ids:
                            rec.write({'current_stage_id': stage.id})
                            stage.write({'status': 'approved'})
                            rec.message_post(
                                body=_("%s has approved  %s.") % (user.name, stage.name),
                                message_type='notification',
                                subtype_xmlid='mail.mt_comment'
                            )
                            break
                if all([status == 'approved' for status in all_stages.mapped('status')]):
                    rec.with_context(button_action=True).write({'status': 'approved'})
                    all_stages.write({'status': 'pending'})

            else:
                before_action_stages = rec.current_stage_id
                current_actions_stages = all_stages.filtered(lambda x: x.sequence > (before_action_stages.sequence - 1))
                if current_actions_stages and user in current_actions_stages[0].user_ids:
                    for stage in current_actions_stages.sorted(key=lambda x: x.sequence):
                        next_stage = current_actions_stages.filtered(lambda x: x.sequence > stage.sequence)
                        if next_stage:
                            rec.write({'current_stage_id': next_stage[0].id})
                            rec.message_post(
                                body=_("%s has approved  %s.") % (user.name, stage.name),
                                message_type='notification',
                                subtype_xmlid='mail.mt_comment'
                            )
                            break
                        else:
                            rec.with_context(button_action=True).write({'status': 'approved'})
        # a=0
        # return True

class DetailUpdate(models.Model):
    _name = "detail.update"
    _description = "Detail Update"
    
    field_name = fields.Char(string='Field Name')
    field_id = fields.Many2one('ir.model.fields', string='Field ID', domain="[('model_id.model', '=', 'hr.employee')]")
    old_value = fields.Char(string='Old Value')
    new_value = fields.Char(string='New Value')
    update_id = fields.Many2one('update.info', string='Update ID')
    
    @api.onchange('field_id')
    def onchange_field_name(self):
        if self.field_id:
            self.old_value = getattr(self.update_id.employee_id, self.field_id.name)
            