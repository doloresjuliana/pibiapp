# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "Nextcloud",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Nextcloud"),
			"hidden": 0
		},
		{
			"module_name": "External Data",
			"color": "grey",
			"icon": "octicon octicon-file-binary",
			"type": "module",
			"label": _("External Data"),
			"hidden": 0
		},
    {
      "module_name": "Redash",
      "color": "grey",
      "icon": "octicon octicon-pulse",
      "type": "module",
      "label": _("Redash"),
      "hidden": 0
    }
	]
