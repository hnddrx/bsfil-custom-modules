{
    'name': 'Employee Medical Record',
    'version': '1.0',
    'summary': 'This module is for managing Employee Medical Records',
    'description': 'A module to list and manage Employee Medical Record',
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
        'advanced_employee_manager',
        'custom_approval_flow',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_medical_record.xml',
        'views/medical_type.xml',
        'data/employee_medical_record.xml',
        
    ], 
    """ "assets":{
        "web.assets_backend":[
            'certificate_of_employment/static/src/js/counter/owl_component.js'
        ] 
    },  """
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}