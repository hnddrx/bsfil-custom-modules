{
    'name': 'Exit Clearance',
    'version': '2.0',
    'summary': 'Clearance of Employee',
    'author': 'Wren',
    'depends': ['base','web','hr'],
    'data': [
            'security/ir.model.access.csv',
            'views/employee_clearance.xml',
            'data/employee_clearance.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
