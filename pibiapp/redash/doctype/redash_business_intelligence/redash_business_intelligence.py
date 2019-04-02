# -*- coding: utf-8 -*-
# Copyright (c) 2019, Dolores Juliana and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class RedashBusinessIntelligence(Document):
	pass

@frappe.whitelist()
def get_dashboard():
	from frappe.utils import has_common
	user_roles = frappe.get_roles()
	list_dashboard = frappe.get_list("Redash Dashboards", fields=["name","title","url_dashboard"], 
		order_by="dborder", ignore_permissions=True)
	out = []
	for dashboard in list_dashboard:
		dashboard_roles = [d.role for d in frappe.get_all("RedashPerm", 
			filters={"parent": dashboard.name}, fields=["role"], ignore_permissions=True)]
		if has_common(user_roles, dashboard_roles):
			out.append([dashboard.title, dashboard.url_dashboard])
	return out
