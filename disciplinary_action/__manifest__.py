{
    'name': "Disciplinary Action",
    'version': '1.0',
    'Summary': 'Disciplinary Action Module',
    'author': "Wren",
    "depends" : [
        'base',
        'web',
        'hr',
        'base_setup',
        'resource',
        'web',
        'mail', 
        'advanced_employee_manager',
        'sanction_list',
        'offense_list'
    ],
    'category': 'Employee Records',
    'description': """
    Description text
    """,
    # data files always loaded at installation
    'data': [
        'views/disciplinary-action-views.xml',
        'security/ir.model.access.csv',
        'data/disciplinary_action_data.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'
}