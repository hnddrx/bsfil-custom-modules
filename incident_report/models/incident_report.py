import random
import string
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date
import urllib.parse  # Import urllib.parse for URL encoding
import logging
_logger = logging.getLogger(__name__)
class IncidentReport(models.Model):
    _name = "incident.report"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Incident Report"
    _rec_name = "doc_name"
    
    #ID
    doc_name = fields.Char(string='Document Name', required=True, readonly=True, default='New', store=True)

    #char fields
    incident_location = fields.Char(string='Incident Location')
    violation_details = fields.Char(string='Violation Details')
    date_and_time_of_offense = fields.Datetime(string='Date and Time of Offense')
    details_of_violation = fields.Text(string='Details of Violation', store=True)
    posting_date = fields.Date(string='Posting Date',required=True,default=lambda self: fields.Datetime.now(),readonly=True)
    damage_done = fields.Text(string='Damage Done')
    involved_employees = fields.One2many(
        'involved.employees',
        'incident_report_id',
        string='Employee'
    )
    reported_by = fields.Many2one('res.users', string="Reported By", default=lambda self: self.env.user)
    date_reported = fields.Date(string="Date Reported", store=True)

    #additional field
    corrective_action = fields.Text(string="Corrective Action")
    employee_category = fields.Selection(string="Employee Category", selection=[('office staff','OFFICE STAFF'),('promodiser','PROMODISER'),('crew','CREW'),('driver/helper/maintenance','DRIVER/HELPER/MAINTENANCE'),('production','PRODUCTION')], store=True)
    department = fields.Many2one('hr.department',string="Department",store=True)
    branch = fields.Char(string="Branch", readonly=True)
    section = fields.Char(string="Section", readonly=True)
    brand  = fields.Char(string="Branch")
    expected_da =  fields.Many2one('sanction.lists', string="Expected Disciplinary Action", store=True)
    
    
    """ Workflow setup """
    current_docstatus = fields.Integer(string="Current Docstatus", default=0)
    current_sequence = fields.Integer(string="Current Sequence", default=0)
    status = fields.Char(string="Status", tracking=True)
    can_approve = fields.Boolean(string="Can Approve", compute="_compute_can_approve_and_reject")
    # can reject - tagging if the approver has a reject button or not 
    can_reject = fields.Boolean(string="Can Reject", compute="_compute_can_approve_and_reject", store=True)
    can_cancel = fields.Boolean(string="Can Cancel", compute="_compute_can_approve_and_reject", store=True)

    work_flow = fields.Many2one('workflow', string='Workflow', compute='_get_workflow', store=True)
    #report_url = fields.Char(string="Report URL", compute="_compute_report_url", store=True)
    module_approval_flow = fields.One2many(
        'incident.approval.flow',
        'incident_id',
        string='Incident Approval Flow'
    )
    
    @api.model
    def open_record(self):
        """Method to explicitly trigger the can_approve calculation on record open"""
        self._compute_can_approve_and_reject()
        
    @api.model
    def _compute_can_approve_and_reject(self):
        """Compute permissions to approve, reject, or cancel based on the current user's role in the approval flow."""
        current_user_id = self.env.user.id  # Fetch the current user ID once for efficiency
        """ Use for record in self: to ensure the method works for multiple records and avoids unexpected single-record assumptions. """
        for record in self:
            # Default all permissions to False
            record.can_approve = record.can_reject = record.can_cancel = False

            # Filter relevant approvers for the current user and sequence
            relevant_approvers = record.module_approval_flow.filtered(
                lambda approver: approver.module_approver_name.id == current_user_id and
                                approver.module_approval_sequence == record.current_sequence
            )

            # Evaluate document status for relevant approvers
            for approver in relevant_approvers:
                if approver.module_doc_status in (1, 2):
                    record.can_approve = True
                elif approver.module_doc_status == 3:
                    record.can_reject = True
                elif approver.module_doc_status == 4:
                    record.can_cancel = True
                """  break  # Exit loop after the first match """
    
    def action_submit(self):
        for record in self:
            if record.status == 'Draft':
                record.update({
                    'current_sequence': 1,
                    'current_docstatus': 1,
                    'date_reported': fields.Datetime.now(),
                    'status': 'Pending',
                })

                
    def action_approve(self):
        for record in self:
            # Filter to find the first matching approver status
            approver_status = record.module_approval_flow.filtered(
                lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status in (1, 2)
            )

            # Update the record if a matching approver is found
            if approver_status:
                approver_status = approver_status[0]  # Get the first matching approver
                approver_status.update({
                    'module_approval_date': fields.Datetime.now(),
                    'module_approval_confirmed': True,
                })
                record.update({
                    'status': approver_status.module_approval_status,
                    'current_docstatus': approver_status.module_doc_status,
                    'current_sequence': record.current_sequence + 1,
                })
    
            
    def action_reject(self):
        for record in self:
            approver_status = record.module_approval_flow.filtered(
                        lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status == 3
                    )
        
            if approver_status:
                    approver_status = approver_status[0]  # Get the first (and presumably only) matching approver
                    record.status = approver_status.module_approval_status
                    record.current_docstatus = approver_status.module_doc_status
                    approver_status.module_approval_date = fields.Datetime.now()
                    approver_status.module_approval_confirmed = True
                    
    def action_cancel(self):
        for record in self:
            approver_status = record.module_approval_flow.filtered(
                        lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status == 4
                    )
        
            if approver_status:
                    approver_status = approver_status[0]  # Get the first (and presumably only) matching approver
                    record.status = approver_status.module_approval_status
                    record.current_docstatus = approver_status.module_doc_status
                    approver_status.module_approval_date = fields.Datetime.now()
                    approver_status.module_approval_confirmed = True

    
    @api.depends('work_flow')
    def _populate_approval_flow(self):
        """Populate or append approval flow records for this ir."""
        for record in self:
            if record.work_flow and record.work_flow.approvals_table:
                approval_values = [
                    {
                        'incident_id': record.id,
                        'module_approver_name': approval.approver_email.id,
                        'module_approver_email': approval.approver_email.login,
                        'module_approval_status': approval.sequence_status.status_name,
                        'module_doc_status': approval.doc_status,
                        'module_approval_sequence': approval.sequence
                    }
                    for approval in record.work_flow.approvals_table
                ]

                # Bulk create missing approvals
                existing_approval_ids = self.env['incident.approval.flow'].search([
                    ('incident_id', '=', record.id),
                    ('module_approval_sequence', 'in', [approval['module_approval_sequence'] for approval in approval_values])
                ]).ids

                # Create new approvals for missing records
                missing_approvals = [approval for approval in approval_values if approval['module_approval_sequence'] not in existing_approval_ids]
                if missing_approvals:
                    self.env['incident.approval.flow'].create(missing_approvals)
                
                if not approval_values:
                    _logger.warning(f"No approval found for ir {record.id}")
            else:
                _logger.warning(f"No approval table found for ir {record.id}")
    #Change to status trigger
    @api.depends('employee_category')
    def _get_workflow(self):
        """Compute and assign the appropriate workflow based on the employee's company."""
        for record in self:
            if not record.employee_category:
                record.work_flow = False
                continue
            # Search for an active workflow matching the company and module selection
            workflow = self.env['workflow'].search(
                [('employee_category', '=', record.employee_category), ('is_active', '=', True), ('module_selection', '=', 'incident_report')],
                limit=1
            )
            
            record.work_flow = workflow.id if workflow else False
    
    """ End of workflow """
    def write(self, vals):
            """Override write to trigger approval flow population when work_flow is updated."""
            res = super(IncidentReport, self).write(vals)
            if 'work_flow' in vals:
                self._populate_approval_flow()
            return res
    @api.model
    def create(self, vals):
        try:
            if vals.get('doc_name', 'New') == 'New':
                sequence_code = 'incident.report'
                company_id = self.env.company.id  # Current company
                # Fetch the correct sequence for the current company
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code)
                ], limit=1)
                if sequence:
                    vals['doc_name'] = sequence.next_by_id()
                else:
                    vals['doc_name'] = '/'  # Fallback if no sequence is found
            
            vals['status'] = 'Draft'  # Set status to Draft by default
            incident = super(IncidentReport, self).create(vals)
            
            if incident.work_flow:
                incident._populate_approval_flow()
            return incident
        except Exception as e: 
            _logger.error("Error creating certificate of employment: %s", e)
            raise


    """ Make NTE  """
    """  def make_nte_offender(self):
        for record in self:
            for involved_employees in record.involved_employees:
                record_data = {}
                if involved_employees.involvement == 'offender':
                    record_data ={
                    }
                
        return False """

    """ End make nte """


""" ir of employment module approval flow """
class IncidentApprovalFlow(models.Model):
    _name = 'incident.approval.flow'
    _description = 'Incident Approval Flow'

    incident_id = fields.Many2one(
        'incident.report',
        string='Incident Report',
        ondelete='cascade'
    )
    module_approver_name = fields.Many2one('res.users', string='Approver Name', store=True)
    module_approver_email = fields.Char(string='Approver Email', store=True)
    module_approval_status = fields.Char(string='Approval Status', store=True)
    module_approval_sequence = fields.Integer(string='Approval Sequence', store=True)
    module_doc_status = fields.Integer(string="Docstatus", store=True)
    module_approval_date =  fields.Datetime(string="Approved On")
    module_approval_confirmed = fields.Boolean(string='Confirmed Approval', store=True)

    
class InvolvedEmployees(models.Model):
    _name = 'involved.employees'
    _description = 'Involved Employees'
    
    incident_report_id = fields.Many2one('incident.report', string="Incident Report")
    employee = fields.Many2one('hr.employee', string="Employee ID", required=True)
    employee_name =  fields.Char(string="Employee Number", readonly=True, compute='_compute_employee_name', store=True)
    involvement  = fields.Selection([('offender', 'Offender'), ('complainant', 'Complainant'), ('witness', 'Witness')],string="Involvement")
    department = fields.Char(string="Department", readonly=True, compute='_compute_employee_name', store=True)
    branch = fields.Char(string="Branch", readonly=True, compute='_compute_employee_name', store=True)
    brand  = fields.Char(string="Brand", readonly=True, compute='_compute_employee_name', store=True)
    
    @api.depends('employee')
    def _compute_employee_name(self):
        for record in self:
            record.employee_name = record.employee.s_employee_id if record.employee else ''
            record.department = record.employee.department_id.name if record.employee else ''
            record.branch = record.employee.x_branch if record.employee else ''
            record.brand = record.employee.x_brand_ if record.employee else''