from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Dashboards"),
			"items": [
				{
					"type": "doctype",
					"name": "Redash Business Intelligence",
					"description": _("It shows the dashboards designed in Redash and enabled in Frappe"),
				}
			]
		},
    {
      "label": _("Settings"),
      "items": [
        {
          "type": "doctype",
          "name": "Redash Dashboards",
          "description": _("List of dashboards and viewing permissions"), 
				}
      ]
    }
]