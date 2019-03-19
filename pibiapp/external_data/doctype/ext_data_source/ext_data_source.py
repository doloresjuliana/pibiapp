# -*- coding: utf-8 -*-
# Copyright (c) 2019, Dolores Juliana and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ExtDataSource(Document):
	def autoname(self):
		if not self.name:
			self.name = 'Ext ' + self.reference_doctype

	def validate(self):
		if not self.row_labels or self.row_labels < 1:
			frappe.throw(_("The row with labels of the columns is a mandatory data."))
		if not self.row_start or self.row_start < 2 or self.row_start < self.row_labels :
			frappe.throw(_("The first row with data to load is a mandatory data and must be after the row that contains the labels."))
		if self.row_stop and self.row_stop <= self.row_start:
			frappe.throw(_("The last row with data to load is not a mandatory data, but if you enter it, it must be greater than the first row of data to be loaded start."))

		if self.import_status == "In Progress":
			frappe.throw(_("Can't save the form as data import is in progress."))
