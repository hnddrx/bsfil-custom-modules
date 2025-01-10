{
    'name': 'Sanction List',
    'version': '1.0',
    'summary': 'This module contains list of sanctions',
    'description': "Contains all the sanctions list that will be fetched in the DA module, it contains offense name and description fields.",
    'category': 'Tools',
    'author': 'Wren',
    'depends': ['base', 'web', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/sanction_list.xml',
        'data/sanction_list.xml',  # Add this line
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'
}