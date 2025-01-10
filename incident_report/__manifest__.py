{
    'name': "Incident Report",
    'version': '1.0',
    'author': "Wren",
    "depends" : ['base', 'web','hr', 'offense_list', 'disciplinary_action', 'sanction_list','workflow'],
    'category': 'Employee Records',
    'description': """
    Description text
    """,
    # data files always loaded at installation
    'data': [
        'security/ir.model.access.csv',
        'views/incident_report.xml',
        'data/incident_report.xml',
    ],
    'installable': True,
    'application': True,
    'images': {
        'icon': 'incident_report/static/description/pn.png',
    },
}