{
    'name': "Notice To Explain",
    'version': '1.0',
    'Summary': 'Notice to Explain',
    'author': "Wren",
    "depends" : [
        'base',
        'web',
        'hr',
        'base_setup',
        'resource',
        'web',
        'mail', 
        'sanction_list',
        'incident_report'
    ],
    'category': 'Employee Records',
    'description': """
    Description text
    """,
    # data files always loaded at installation
    'data': [
        'views/notice-to-explain-views.xml',
        'security/ir.model.access.csv',
        'data/notice_to_explain_data.xml'
    ],
    """ "assets":{
        "web.assets_backend":[
            'notice_to_explain/static/src/js/owl_component_nte.js'
        ]
    }, """
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3'
}