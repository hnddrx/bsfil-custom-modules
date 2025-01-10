from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class Workflow(models.Model):
    _name = 'workflow'
    _description = 'Workflow'
    _rec_name = 'doc_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Fields
    doc_name = fields.Char(
        string="Document Name", 
        required=True, 
        tracking=True
    )
    module_selection = fields.Selection(
        selection="_get_available_modules",
        string="Select Module",
        required=True,
        tracking=True
    )
    
    #?? Remove this field, it is not necessary to have this 
    # Conclusion: if we have multiple approval levels that makes the workflow sequential and if we want to make it parallel we simply put the sequence number into 1. why? E.g., 5 approvers same sequence number either of them can approve
    action_flow = fields.Selection(
        selection=[('parallel', 'Parallel'), ('sequential', 'Sequential')],
        string="Action Flow",
        required=True,
        tracking=True
    )
    is_active = fields.Boolean(
        string="Is Active", 
        default=True,
    )
    approvals_table = fields.One2many(
        'approvals',
        'workflow_id',
        string='Approval Table'  
    )
    
    companies_table = fields.One2many(
        'multiple.companies',
        'workflow_id',
        string="Companies Table"
    )
    

    @api.model
    def _get_available_modules(self):
        """Fetch installed modules for the selection field."""
        modules = self.env['ir.module.module'].search([('state', '=', 'installed')])
        if not modules:
            _logger.warning("No installed modules found.")
            return []
        return [(module.name, module.shortdesc or module.name) for module in modules]
    
class Approvals(models.Model):
    _name = 'approvals'
    _description = 'Approval Records'

    workflow_id = fields.Many2one(
        'workflow',
        string='Workflow',
        required=True,
        ondelete='cascade'
    )
    approver_email = fields.Many2one(
        'res.users',
        string='Approver Email',
        required=True
    )
    """ ('company_id', 'in', workflow_id.company), """
    sequence_status = fields.Many2one(
        'docstatus',
        string='Approval Status',
        tracking=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=1,
        required=True
    )

    
    doc_status = fields.Integer(
        string="Docstatus", 
        compute='_get_doc_status',
        help="1 - Approval in progress\n"
            "2 - Approved\n"
            "3 - Rejected\n"
            "4 - Cancelled\n"
            "5 - Soft Delete"
    )
    
    @api.depends('sequence_status.doc_status')
    def _get_doc_status(self):
        for record in self:
            record.doc_status = record.sequence_status.doc_status or 0

#Create tabler for company
class MultipleCompanies(models.Model):
    _name = "multiple.companies"
    _description = "Multiple Companies"
    
    workflow_id = fields.Many2one(
        'workflow',
        string='Workflow',
        required=True,
        ondelete='cascade'
    )
    
    company =  fields.Many2one('res.company', string="Company", required=True)
    
    
    

