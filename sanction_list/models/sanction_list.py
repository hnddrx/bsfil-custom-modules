from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
class SanctionList(models.Model):
    _name = 'sanction.lists'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sanction Lists'
    _rec_name = "doc_name"
    
    doc_name = fields.Char(string='Document Name', required=True, readonly=True, default='New')
    sanction_name = fields.Char(string='Sanction Name', required=True, track_visibility='onchange')
    description = fields.Text(string='Description', required=True, track_visibility='onchange')
    
    
    @api.model
    def create(self, vals):
        # Automatically generate doc_name using offense_name if it's 'New'
        if vals.get('doc_name', 'New') == 'New':
            vals['doc_name'] = vals.get('sanction_name', '/')
        return super(SanctionList, self).create(vals)
    
    def action_save(self):
        """Custom save action."""
        self.ensure_one()
        _logger.info(f"Saving Employment Certificate: {self.doc_name}")