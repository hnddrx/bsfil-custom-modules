from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date
import urllib.parse  # Import urllib.parse for URL encoding
import logging

_logger = logging.getLogger(__name__)

class NoticeToExplain(models.Model):
    _name = "notice.to.explain"
    _description = "Notice to Explain"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'

    doc_name = fields.Char(string="Name", readonly=True, default='New')

    # Many2many relationship field for incident reports
    incident_report = fields.Many2one('incident.report', string='Incident Report')

    # Many2one relationship field for the employee
    employee = fields.Many2one('hr.employee', string='Employee', required=True)

    employee_name = fields.Char(string='Employee Name', readonly=True, compute='_compute_employee_name', store=True)
    employee_category = fields.Char(string="Employee Category", store=True)
    # Attachments related to this document
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Attachments",
        help="Attachments related to this document"
    )

    remarks = fields.Text(string=_("Explanation"))

    # Additional fields for confirmation
    date_of_explanation = fields.Date(string="Date of explanation")
    date_of_nte = fields.Date(string="Date of issued NTE")
    number_of_days = fields.Date(string="Number of days")

    # Posting date (current date by default)
    posting_date = fields.Date(string="Posting date", default=lambda self: date.today())
    #Report URL 
    report_url = fields.Char(string="Report URL", compute="_compute_report_url", store=True)
    """ Workflow Setup """
    current_docstatus = fields.Integer(string="Current Docstatus", default=0)
    current_sequence = fields.Integer(string="Current Sequence", default=0)
    status = fields.Char(string="Status", tracking=True)
    can_approve = fields.Boolean(string="Can Approve", compute="_compute_permissions", store=True)
    can_reject = fields.Boolean(string="Can Reject", compute="_compute_permissions", store=True)
    can_cancel = fields.Boolean(string="Can Cancel", compute="_compute_permissions", store=True)

    work_flow = fields.Many2one('workflow', string='Workflow', compute='_compute_workflow', store=True)
    module_approval_flow = fields.One2many(
        'notice.approval.flow',
        'notice_id',
        string='Module Approval Flow'
    )
    
    """ Generate jasper report """
    
    def _compute_report_url(self):
        """Private method to compute the report URL."""
        for record in self:
            base_url = 'http://192.168.2.161:8080/jasperserver/flow.html'
            params = {
                '_flowId': 'viewReportFlow',
                'ParentFolderUri': '/Forms',
                'reportUnit': '/forms/notice_to_explain',
                'standAlone': 'true',
                'j_username': 'jasperadmin',
                'j_password': 'jasperadmin',
                'output': 'pdf',
                'filter1': record.doc_name or ''
            }
            # Construct the full URL with query parameters
            record.report_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    def action_generate_report_url(self):
        """Public method to be called by the button."""
        self._compute_report_url()
        # Optionally return an action or response
        return {
            'type': 'ir.actions.act_url',
            'url': self.report_url,
            'target': 'new',  # Opens in a new tab
        }
        
    """ End Generate Report  """

    @api.model
    def open_record(self):
        """Method to explicitly trigger the can_approve calculation on record open"""
        try:
            self._compute_permissions()
            
        except Exception as e:
            _logger.error("Error in open_record: %s", e)
            raise
        
    @api.depends('status')
    def _compute_permissions(self):
        """Compute permissions to approve, reject, or cancel based on the current user's role in the approval flow."""
        current_user_id = self.env.user.id
        for record in self:
            try:
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
            except Exception as e:
                _logger.error("Error in _compute_permissions for record %s: %s", record.id, e)
                raise

    def action_submit(self):
        """Action to submit the notice."""
        for record in self:
            try:
                if record.status == 'Draft':
                    record.status = 'Pending'
                    record.current_sequence += 1
                    record.current_docstatus += 1
            except Exception as e:
                _logger.error("Error in action_submit for record %s: %s", record.id, e)
                raise

    def action_approve(self):
        """Action to approve the notice."""
        for record in self:
            try:
                approver_status = record.module_approval_flow.filtered(
                    lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status in (1, 2)
                )

                if approver_status:
                    approver_status = approver_status[0]  # Get the first matching approver
                    record.status = approver_status.module_approval_status
                    record.current_docstatus = approver_status.module_doc_status
                    approver_status.module_approval_date = fields.Datetime.now()
                    approver_status.module_approval_confirmed = True
                    record.current_sequence += 1
            except Exception as e:
                _logger.error("Error in action_approve for record %s: %s", record.id, e)
                raise

    def action_reject(self):
        """Action to reject the notice."""
        for record in self:
            try:
                approver_status = record.module_approval_flow.filtered(
                    lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status == 3
                )

                if approver_status:
                    approver_status = approver_status[0]  # Get the first matching approver
                    record.status = approver_status.module_approval_status
                    record.current_docstatus = approver_status.module_doc_status
                    approver_status.module_approval_date = fields.Datetime.now()
                    approver_status.module_approval_confirmed = True
            except Exception as e:
                _logger.error("Error in action_reject for record %s: %s", record.id, e)
                raise

    def action_cancel(self):
        """Action to cancel the notice."""
        for record in self:
            try:
                approver_status = record.module_approval_flow.filtered(
                    lambda a: a.module_approver_name.id == self.env.user.id and a.module_doc_status == 4
                )

                if approver_status:
                    approver_status = approver_status[0]  # Get the first matching approver
                    record.status = approver_status.module_approval_status
                    record.current_docstatus = approver_status.module_doc_status
                    approver_status.module_approval_date = fields.Datetime.now()
                    approver_status.module_approval_confirmed = True
            except Exception as e:
                _logger.error("Error in action_cancel for record %s: %s", record.id, e)
                raise
            
    def _populate_approval_flow(self):
        """Populate the approval flow based on the workflow."""
        # Add logic to populate the approval flow here
        """Populate or append approval flow records for this certificate."""
        for record in self:
            if record.work_flow and record.work_flow.approvals_table:
                approval_values = [
                    {
                        'notice_id': record.id,
                        'module_approver_name': approval.approver_email.id,
                        'module_approver_email': approval.approver_email.login,
                        'module_approval_status': approval.sequence_status.status_name,
                        'module_doc_status': approval.doc_status,
                        'module_approval_sequence': approval.sequence
                    }
                    for approval in record.work_flow.approvals_table
                ]

                # Bulk create missing approvals
                existing_approval_ids = self.env['module.approval.flow'].search([
                    ('notice_id', '=', record.id),
                    ('module_approval_sequence', 'in', [approval['module_approval_sequence'] for approval in approval_values])
                ]).ids

                # Create new approvals for missing records
                missing_approvals = [approval for approval in approval_values if approval['module_approval_sequence'] not in existing_approval_ids]
                if missing_approvals:
                    self.env['module.approval.flow'].create(missing_approvals)
                    _logger.info(f"Approval flow appended for certificate {record.id}")
                
                if not approval_values:
                    _logger.warning(f"No approval found for certificate {record.id}")
            else:
                _logger.warning(f"No approval table found for certificate {record.id}")
        pass

    @api.depends('employee_category')
    def _compute_workflow(self):
        """Compute and assign the appropriate workflow based on the employee's company."""
        for record in self:
            if not record.employee:
                record.work_flow = False
                continue

            employee_data = record.employee.read(['company_id'])[0]
            company_id = employee_data.get('company_id', [False])[0]

            # Search for an active workflow matching the company and module selection
            workflow = self.env['workflow'].search(
                [('company', '=', company_id), ('is_active', '=', True), ('module_selection', '=', 'notice_to_explain')],
                limit=1
            )

            if workflow:
                record.work_flow = workflow.id
            else:
                record.work_flow = False
                
    @api.depends('employee')
    def _compute_employee_name(self):
        """Compute the employee name based on the selected employee."""
        for record in self:
            if record.employee:
                record.employee_name = record.employee.name
                record.employee_category = record.employee.x_employeecategory_
            else:
                record.employee_name = ''
                record.employee_category = ''
                
    @api.onchange('attachment_ids')
    def _onchange_attachment_ids(self):
        """Automatically handle attachment upload and associate it with this record."""
        for attachment in self.attachment_ids:
            attachment.res_model = self._name
            attachment.res_id = self.id
            
    @api.model
    def create(self, vals):
        """Create method override with error handling and approval flow population."""
        try:
            if vals.get('doc_name', 'New') == 'New':
                sequence_code = 'notice.to.explain'
                company_id = self.env.company.id  # Current company
                # Fetch the correct sequence for the current company
                sequence = self.env['ir.sequence'].sudo().search([('code', '=', sequence_code)], limit=1)
                if sequence:
                    vals['doc_name'] = sequence.next_by_id()
                else:
                    vals['doc_name'] = '/'  # Fallback if no sequence is found

            vals['status'] = 'Draft'  # Set status to Draft by default
            notice = super(NoticeToExplain, self).create(vals)

            if notice.work_flow:
                notice._populate_approval_flow()
            return notice
        except Exception as e:
            _logger.error("Error creating notice to explain: %s", e)
            raise

    def write(self, vals):
        """Override write to trigger approval flow population when work_flow is updated."""
        try:
            res = super(NoticeToExplain, self).write(vals)
            if 'work_flow' in vals:
                self._populate_approval_flow()
            return res
        except Exception as e:
            _logger.error("Error updating notice to explain: %s", e)
            raise
        
            
            
""" Notice to explain module approval flow """
class NoticeApprovalFlow(models.Model):
    _name = 'notice.approval.flow'
    _description = 'Notice Approval Flow'

    notice_id = fields.Many2one(
        'notice.to.explain',
        string='Notice to explain'
    )
    module_approver_name = fields.Many2one('res.users', string='Approver Name', store=True)
    module_approver_email = fields.Char(string='Approver Email', store=True)
    module_approval_status = fields.Char(string='Approval Status', store=True)
    module_approval_sequence = fields.Integer(string='Approval Sequence', store=True)
    module_doc_status = fields.Integer(string="Docstatus", store=True)
    module_approval_date =  fields.Datetime(string="Approved On")
    module_approval_confirmed = fields.Boolean(string='Confirmed Approval', store=True)    
