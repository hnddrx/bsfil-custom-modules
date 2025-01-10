{
    'name': 'Employee Accountability',
    'version': '1.0',
    'summary': 'Employee Accountability',
    'depends': ['base','web','hr', 'custom_approval_flow'],
    'author': 'Wren',
    'data': [
            'security/ir.model.access.csv',
            'views/employee_accountability.xml',
            'data/employee_accountability.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
     'license': 'LGPL-3'
}
