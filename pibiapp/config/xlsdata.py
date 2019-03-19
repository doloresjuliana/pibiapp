from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Xls File to Load",
					"description": _("Load Excel files as new doctype of Frappe"),
				}
			]
		}
]
