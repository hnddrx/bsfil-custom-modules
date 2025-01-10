{
    'name': 'Custom  Approval flow',
    'version': '1.0',
    'summary': 'This module is for managing Approval flow for each module application',
    'description': 'A module to list and manage approval flow for each module application',
    'category': 'Human Resource',
    'author': 'Wren',
    'depends': [
        'base', 
        'web', 
        'hr',
        'base_setup',
        'resource',
        'web',
        'mail',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/docstatus.xml',
        'views/workflow.xml'
      
        
    ], 
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'
}