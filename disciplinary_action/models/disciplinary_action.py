import random
import string
from odoo import fields, models, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class DisciplinaryAction(models.Model):
    _name = "disciplinary.action"
    _description = "Disciplinary Action"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'
    
    
    doc_name = fields.Char(string="Name", readonly=True, default='New')
    
    # Many2one relationship field
    incident_report = fields.Many2one('incident.report', string='Incident Report',required=True)
    
    sanction = fields.Many2one('sanction.lists', string='Sanction', required=True)
    description = fields.Char(string='Sanction Description', readonly=True, compute='_get_sanction', store=True)
    next_sanction = fields.Many2one('sanction.lists', string='Next Sanction')
    next_sanction_description = fields.Char(string='Sanction Description', readonyl=True, compute='_get_sanction', store=True)
    underwent_preventive_suspension = fields.Boolean(string="Underwent to Preventive Suspension", default=False)
    underwent = fields.Boolean(string='Underwent to a conference', default=False)
    offense = fields.Many2one('offense.lists', string='Offense',required=True)
    offense_description = fields.Char(string='Offense Description', readonly=True, compute='_get_offense', store=True)
    
    terminated_on = fields.Date(string='Terminated On')

    employee = fields.Many2one('hr.employee',string='Employee', required=True)
    employee_name = fields.Char(string='Employee Number', readonly=True, compute='_compute_employee_info', store=True)
    department = fields.Char(string='Department', readonly=True, compute = '_compute_employee_info', store=True)
    branch = fields.Char(string='Branch', readonly=True, compute = '_compute_employee_info', store=True )
    brand = fields.Char(string="Brand", readonly=True, compute = '_compute_employee_info', store=True )
    number_of_days = fields.Integer(string='Number of Suspension Days')
    posting_date = fields.Date(string='Posting Date', default=fields.Date.context_today, readonly=True)
    suspended_from = fields.Date(string='Suspended From')
    suspended_to = fields.Date(string='Suspended To')
    
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        string="Attachments", 
        help="Attachments related to this document"
    )
    
    #Text fields
    hearing_remarks = fields.Text(string='Hearing Remarks')
    remarks = fields.Text(string='Remarks')
    
    """ Put needed workflow fields """
    
    """ End of workflow fild """
    
    """ put workflow logic here """

    """ End of workflow """
    
    @api.model
    def create(self, vals):
        """Generate document name sequence during creation."""
        if vals.get('doc_name', 'New') == 'New':
                sequence_code = 'disciplinary.action'
                company_id = self.env.company.id  # Current company
                # Fetch the correct sequence for the current company
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code)
                ], limit=1)
                if sequence:
                    vals['doc_name'] = sequence.next_by_id()
                else:
                    vals['doc_name'] = '/'  # Fallback if no sequence is found
            
            
        return super(DisciplinaryAction, self).create(vals)

    """   @api.depends('incident_report')
    def _compute_offense(self):
        for record in self:
            record.incident_report_description = record.offense.description if record.offense else ''
            
            """ 
    @api.depends('employee')
    def _compute_employee_info(self):
        for record in self:
            employee = record.employee
            if employee:
                record.employee_name = employee.s_employee_id
                record.department = employee.department_id.name
                record.branch = employee.x_branch
                record.brand = employee.x_brand_

            else:
                record.employee_name = ''
                record.department = ''
                record.branch = ''
                record.brand = ''
            
    @api.depends('sanction','next_sanction')
    def _get_sanction(self):
        for record in self:
            record.description = record.sanction.description if record.sanction else ''
            record.next_sanction_description = record.next_sanction.description if record.next_sanction else ''
            
    @api.depends('offense')
    def _get_offense(self):
        for record in self:
            record.offense_description = record.offense.description if record.offense else '' 

