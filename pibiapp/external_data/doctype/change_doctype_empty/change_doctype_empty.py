# -*- coding: utf-8 -*- Copyright (c) 2019, Dolores Juliana and contributors For license information, please see 
# license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class ChangeDocTypeEmpty(Document):
	def validate(self):
		numrecords = frappe.db.count(self.reference_doctype)
		if numrecords and numrecords > 0:
			frappe.throw(_("{0} is not empty contains {1} records. You can not make changes until you empty it.").format(self.reference_doctype,numrecords))

		if not frappe.db.table_exists(self.name) and not self.docfield:
			allfields = frappe.get_list('DocField', filters={'parent': self.reference_doctype}, fields="*")
			for onefield in allfields:
				datadoc = onefield
				#frappe.throw((self.name + " -> " + str(datadoc)))
				datadoc['doctype'] = 'Change DocField'
				datadoc['parent'] = self.name
				del datadoc['name']
				doc = frappe.get_doc(datadoc)
				self.append ("docfield", doc)
