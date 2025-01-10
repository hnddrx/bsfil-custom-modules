from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class EmployeeAccountability(models.Model):
    _name = 'accountability'
    _description = 'Employee Accountability'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'doc_name'

    # Fields
    doc_name = fields.Char(string="Document Name", readonly=True, default='New', copy=False)
    employee = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        context={'no_create': True}
    )
    
    
    first_name = fields.Char(string="First Name", readonly=True, compute='_compute_employee_info', store=True)
    last_name = fields.Char(string="Last Name", readonly=True, compute='_compute_employee_info', store=True)
    department = fields.Char(string='Department', readonly=True, compute='_compute_employee_info', store=True)
    company = fields.Char(string='Company', readonly=True, compute='_compute_employee_info', store=True)
    posting_date = fields.Date(string='Posting Date', default=fields.Date.today)
    accountability_type = fields.Selection([
        ('issuance', 'Issuance'),
        ('return', 'Return'),
    ], string='Type', required=True, default='issuance')
    
    issuance_table = fields.One2many(
        'issuance',
        'accountability_id',
        string='Issuance Table'
    )
    
    return_table = fields.One2many(
        'return',
        'accountability_id',
        string='Return Table'
    )

    remarks = fields.Text(string="Remarks")
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Attachments",
        help="Attachments related to this document"
    )

    
    # Override create method
    @api.model
    def create(self, vals):
        if vals.get('doc_name', 'New') == 'New':
                sequence_code = 'accountability'
                company_id = self.env.company.id  # Current company
                # Fetch the correct sequence for the current company
                sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', sequence_code)
                ], limit=1)
                if sequence:
                    vals['doc_name'] = sequence.next_by_id()
                else:
                    vals['doc_name'] = '/'  # Fallback if no sequence is found
        record = super(EmployeeAccountability, self).create(vals)
        
        # Auto-fill company and department based on employee
        if record.employee:
            record.company = record.employee.company_id.name
            record.department = record.employee.department_id.name

        return record

    @api.depends('employee')
    def _compute_employee_info(self):
        for record in self:
            if record.employee:
                record.department = record.employee.department_id.name
                record.company = record.employee.company_id.name
                record.first_name = record.employee.s_first_name
                record.last_name = record.employee.s_last_name
            else:
                record.department = ''
                record.company = ''
                record.first_name = ''
                record.last_name = ''

    @api.onchange('accountability_type')
    def _onchange_accountability_type(self):
        if self.accountability_type == 'return':
            # Fetch the latest issuance records for this employee
            last_issuance = self.env['accountability'].search([
                ('employee', '=', self.employee.id),
                ('accountability_type', '=', 'issuance')
            ], limit=1, order='posting_date desc')

            if last_issuance:
                # Clear current return table and populate it with items that still have remaining quantities
                self.return_table = [(5, 0, 0)]
                return_entries = []
                
                for issuance in last_issuance.issuance_table:
                    # Calculate the total returned quantity for this item
                    returned_quantity = sum(self.env['return'].search([
                        ('accountability_id.employee', '=', self.employee.id),
                        ('item_name', '=', issuance.item_name)
                    ]).mapped('quantity'))
                    
                    # Calculate remaining quantity
                    remaining_quantity = issuance.quantity - returned_quantity

                    if remaining_quantity > 0:
                        return_entries.append((0, 0, {
                            'item_name': issuance.item_name,
                            'item_code': issuance.item_code,
                            'quantity': remaining_quantity,
                            'date_issued': issuance.date_issued,
                        }))

                self.return_table = return_entries

class Issuance(models.Model):
    _name = 'issuance'
    _description = 'Issuance'

    accountability_id = fields.Many2one('accountability', string="Accountability ID")
    item_name = fields.Char(string="Item Name")
    item_code = fields.Char(string="Item Code")
    quantity = fields.Integer(string="Quantity")
    date_issued = fields.Date(string="Date Issued")

class Return(models.Model):
    _name = 'return'
    _description = 'Return'

    accountability_id = fields.Many2one('accountability', string="Accountability ID")
    item_name = fields.Char(string="Item Name")
    item_code = fields.Char(string="Item Code")
    quantity = fields.Integer(string="Quantity")
    date_issued = fields.Date(string="Date Issued")
    return_to = fields.Many2one('hr.employee', string='Return To')
    date_returned = fields.Date(string='Date Returned')
