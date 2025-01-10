from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date
import urllib.parse  # Import urllib.parse for URL encoding
import logging

_logger = logging.getLogger(__name__)

class EmployeeClearance(models.Model):
    _name = 'employee.clearance'
    _description = 'Employee Clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'

    # Employee Clearance Name
    doc_name = fields.Char(string="Document Name", readonly=True, default='New', copy=False)

    # Employee Information
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    employee_name = fields.Char(string="Employee Name", readonly=True, compute='_compute_employee_info', store=True)
    position_title = fields.Char(string="Position Title", readonly=True, compute='_compute_employee_info', store=True)
    employment_status = fields.Char(string="Employee Status", readonly=True, compute='_compute_employee_info', store=True)
    company = fields.Char(string="Company", readonly=True, compute='_compute_employee_info', store=True)
    department = fields.Char(string="Department", readonly=True, compute='_compute_employee_info', store=True)

    #Report URL 
    report_url = fields.Char(string="Report URL", compute="_compute_report_url", store=True)
    
    #Clearance Information
    reason_for_leaving = fields.Text(string="Reason for Leaving")
    company_email = fields.Char(string="Company Email", readonly=True, compute='_compute_employee_info', store=True)
    remarks = fields.Text(string="Remarks")
    last_working_date = fields.Date(string="Last Working Date")
    effective_date = fields.Date(string="Effective Date")
    posting_date = fields.Date(string='Posting Date', default=fields.Date.context_today, readonly=True)
    consent = fields.Boolean(string='Consent')
    
    # Clearance Type and Authorizations
    clearance_type = fields.Selection(
        [
            ('Resignation', 'Resignation'),
            ('Retirement', 'Retirement'),
            ('Regularization', 'Regularization'),
            ('Termination', 'Termination'),
        ], 
        string='Clearance Type', 
        required=True
    )
    
    authorize_ids = fields.One2many(
        'department.manager',
        'clearance_id',  # Corrected reverse relation field
        string='Authorized',
    )
    
    human_resource_ids = fields.One2many(
        'human.resources',
        'clearance_id',  # Corrected reverse relation field
        string='Authorized',
        copy=True
    )


    # Signee Information
    conforme_employee_name = fields.Many2one('hr.employee', string='Conforme', readonly=True)
    contact_number = fields.Char(string='Contact Number')
    signed_date = fields.Date(string='Signed Date', compute='_compute_signed_date', store=True)  # Date field instead of Char


    """ Generate jasper report """
    
    def _compute_report_url(self):
        """Private method to compute the report URL."""
        for record in self:
            base_url = 'http://192.168.2.161:8080/jasperserver/flow.html'
            params = {
                '_flowId': 'viewReportFlow',
                'ParentFolderUri': '/Forms',
                'reportUnit': '/forms/clearance',
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
    def create(self, vals):
        """Generate document name sequence during creation."""
        if vals.get('doc_name', 'New') == 'New':
                sequence_code = 'employee.clearance'
                company_id = self.env.company.id  # Current company
                # Fetch the correct sequence for the current company
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code)
                ], limit=1)
                if sequence:
                    vals['doc_name'] = sequence.next_by_id()
                else:
                    vals['doc_name'] = '/'  # Fallback if no sequence is found
        return super(EmployeeClearance, self).create(vals)

    def action_save(self):
        """Custom save action."""
        self.ensure_one()
        _logger.info(f"Saving Employee Clearance {self.doc_name}")

    @api.depends('consent')
    def _compute_signed_date(self):
        for record in self:
            if record.consent:
                record.signed_date = fields.Date.context_today(self)
            else:
                record.signed_date = False
        

    @api.depends('employee_id')
    def _compute_employee_info(self):
        """Compute employee-related fields."""
        for record in self:
            employee = record.employee_id
            if employee:
                record.employee_name = employee.s_full_name
                record.department = employee.department_id.name
                record.company = employee.company_id.name
                record.company_email = employee.s_corporate_email
                record.position_title = employee.job_title
                record.conforme_employee_name = employee
            else:
                record.employee_name = ''
                record.department = ''
                record.company = ''
                record.company_email = ''
                record.position_title = ''
                record.conforme_employee_name = ''
                
class DepartmentManager(models.Model):
    _name = 'department.manager'
    _description = 'Department Manager Clearance'

    # Link back to the clearance record
    clearance_id = fields.Many2one(
        'employee.clearance', 
        string="Clearance", 
        required=True, 
        ondelete='cascade'
    )    

    # Clearance Details
    authorized = fields.Many2one(
        'res.users', 
        string='Authorized', 
        compute="_compute_authorized", 
        store=False,  # Remove if not needed to store in DB
    )
    
    status = fields.Selection(
        selection=[
            ('cleared', 'Cleared'), 
            ('not-cleared', 'Not Cleared')
        ], 
        string="Status"
    )
    remarks = fields.Text(string='Remarks')
    date = fields.Date(string="Date", compute="_compute_authorized", store=False)

    accountability = fields.Selection(
        string="Accountability",
        selection=[('job_turn_over','Job turn-over Checklist')],
        help="Automatically populated based on the selected department"
    )
    
    @api.depends('status')
    def _compute_authorized(self):
        for record in self:
            if record.status == 'cleared':
                record.authorized = self.env.user
                record.date = fields.Date.context_today(self)
            else:
                record.authorized = False
                record.date = False
                
    @api.depends('status')
    def _compute_authorized(self):
        for record in self:
            if record.status:
                record.authorized = self.env.user
                record.date = fields.Date.context_today(self)
            else:
                record.authorized = False
                record.date = False

class HumanResources(models.Model):
    _name = 'human.resources'
    _description = 'Human Resources Clearance'

    # Link back to the clearance record
    clearance_id = fields.Many2one(
        'employee.clearance', 
        string="Clearance", 
        required=True, 
        ondelete='cascade'
    )    

    # Clearance Details
    authorized = fields.Many2one(
        'res.users', 
        string='Authorized', 
        compute="_compute_authorized", 
        store=False,  # Remove if not needed to store in DB
    )
    
    status = fields.Selection(
        selection=[
            ('cleared', 'Cleared'), 
            ('not-cleared', 'Not Cleared')
        ], 
        string="Status"
    )
    remarks = fields.Text(string='Remarks')
    date = fields.Date(string="Date", compute="_compute_authorized", store=False)

    accountability = fields.Selection(
        string="Accountability",
        selection=[],
        help="Automatically populated based on the selected department"
    )
    
    @api.depends('status')
    def _compute_authorized(self):
        for record in self:
            if record.status == 'cleared':
                record.authorized = self.env.user
                record.date = fields.Date.context_today(self)
            else:
                record.authorized = False
                record.date = False
                
    @api.depends('status')
    def _compute_authorized(self):
        for record in self:
            if record.status:
                record.authorized = self.env.user
                record.date = fields.Date.context_today(self)
            else:
                record.authorized = False
                record.date = False


