from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class OffenseLists(models.Model):
    _name = 'offense.lists'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Offense Lists'
    _rec_name = "doc_name"
    
    doc_name = fields.Char(string='Document Name', required=True, readonly=True, default='New')
    offense_name = fields.Char(string='Offense Name', required=True, tracking=True, store=True)
    description = fields.Text(string='Description', required=True, tracking=True, store=True)
    
    @api.model
    def create(self, vals):
        # Automatically generate doc_name using offense_name if it's 'New'
        if vals.get('doc_name', 'New') == 'New':
            vals['doc_name'] = vals.get('offense_name', '/')
        
        return super(OffenseLists, self).create(vals)

    def action_save(self):
        """Custom save action."""
        self.ensure_one()
        _logger.info(f"Saving Offense List: {self.doc_name}")
