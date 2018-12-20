from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Nextcloud Settings",
					"description": _("Connect Nexcloud with Frappe apps"),
				}
			]
		}
]
