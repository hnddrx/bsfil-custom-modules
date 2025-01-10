from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class Docstatus(models.Model):
    _name = 'docstatus'
    _description = 'Document Status'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'status_name'

    status_name = fields.Char(
        string="Status Name", 
        required=True, 
        tracking=True
    )

    doc_status_name = fields.Selection(
        string="Docstatus Name", 
        selection=[
            ('ongoing', 'Ongoing'), 
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('cancel', 'Cancel'),
            ('delete', 'Delete')
        ],
        required=True,
        tracking=True
    )

    doc_status = fields.Integer(
        string="Docstatus", 
        compute="_compute_doc_status", 
        store=True, 
        tracking=True
    )

    @api.depends('doc_status_name')
    def _compute_doc_status(self):
        """Automatically sets doc_status based on doc_status_name."""
        # Define a mapping for doc_status_name to doc_status
        status_mapping = {
            'ongoing': 1,
            'approve': 2,
            'reject': 3,
            'cancel': 4,
            'delete': 5,
        }
        
        for record in self:
            # Use the mapping to set doc_status, default to 0 if not found
            record.doc_status = status_mapping.get(record.doc_status_name, 0)
