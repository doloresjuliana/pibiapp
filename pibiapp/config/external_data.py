from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("External Data"),
			"items": [
				{
					"type": "doctype",
					"name": "Ext Data Source",
					"description": _("Load files as new doctype of Frappe"),
				},
				{
					"type": "doctype",
					"name": "Successive loads",
					"description": _("Reload external data"),
				}
			]
		}
]
