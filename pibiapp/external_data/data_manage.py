# Copyright (c) 2019, Dolores Juliana Fdez Martin
# License: GNU General Public License v3. See license.txt
#
# This file is part of Pibiapp_Nextcloud.
#
# Pibiapp_Nextcloud is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as 
# published by the Free Software Foundation, version 3 of the License.
#
# Pibiapp_Nextcloud is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY  or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License 
# along with Pibiapp_Nextcloud included in the license.txt file. 
# If not, see <https://www.gnu.org/licenses/>.

from __future__ import unicode_literals
import frappe, ast
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
from frappe.utils.csvutils import read_csv_content
import six
from datetime import date, datetime
from xml.etree import ElementTree as ET

def loaddata(self, method=None):
	ext_rows = readfile(file_url=self.import_file, data_format=self.data_format)
	if not frappe.db.exists('DocType', self.name): newdata = True
	else: newdata = False
	datarows = analyzedata(row_labels=self.row_labels, row_start=self.row_start, ext_rows=ext_rows, 
		row_stop=self.row_stop, newdata=newdata, name=self.name, module=self.module)
	if self.not_load:
		numrecords = 0
	else:
		numrecords = addrecords(name=self.name, datarows=datarows)
	message = str(numrecords) + ' records loaded in the DocType ' + self.name
	frappe.publish_realtime('msgprint', message )
	
def reloaddata(self, method=None):
	ext_rows = readfile(file_url=self.import_file, data_format=self.data_format)
	row_stop = 0 if self.row_end == 0 else self.row_start + self.row_end - 1
	datarows = analyzedata(row_labels=self.row_labels, row_start=self.row_start + self.rows_ignored, 
		ext_rows=ext_rows, row_stop=row_stop, newdata=False, 
		name=self.reference_doctype, module=self.module)
	self.records = addrecords(name=self.reference_doctype, datarows=datarows)
	message = str(self.records) + ' records loaded in the DocType ' + self.reference_doctype
	self.loading_time = frappe.utils.data.now()
	self.save()
	frappe.publish_realtime('msgprint', message )

def readfile(file_url, data_format, fcontent=None, filepath=None):
	if data_format == "XLSX":
		ext_rows = read_xlsx_file_from_attached_file(file_url, fcontent, filepath)
	else:
		file_att = frappe.get_doc("File", {"file_url": file_url})
		filename = file_att.get_full_path()
	if data_format == "CSV":
		with open(filename, "r") as infile:
			ext_rows = read_csv_content(infile.read())
	if data_format == "JSON":
		with open(filename, 'r') as infile:
			try:
				aa = str(infile.read())
				aa = aa.replace("[","").replace("]","").replace(",{","#{").split("#")
				ext_rows = []
				ext_rows.append([])
				j = 1
				while j <= len(aa):
					bb = ast.literal_eval(aa[j - 1])
					ext_rows.append([])
					for x in bb.values():
						ext_rows[j].append(str(x))
					j += 1
				bb = ast.literal_eval(aa[0])
				for x, y in bb.items():
					ext_rows[0].append(str(x))
			except ValueError:
				print("bad json: {0}".format(file_url))
				raise
	if data_format == "XML":
		with open(filename, 'r') as infile:
			try:
				tree = ET.parse(infile)
				root = tree.getroot()
				ext_rows = []
				ext_rows.append([])
				for child in root[0]:
					ext_rows[0].append(str(child.tag))
				i = 0
				for child in root:
					ext_rows.append([])
					i += 1
					for subchild in child:
						ext_rows[i].append(str(subchild.text))
			except ValueError:
				print("bad xml: {0}".format(file_url))
				raise
	if ext_rows:
		if not isinstance(ext_rows, list):
			ext_rows = [ext_rows]
	return ext_rows

def analyzedata(row_labels, row_start, ext_rows, row_stop=None, newdata=False, name=None, module=None):
	xrow = 0
	tt = []
	labels = []
	lengths = []
	datatypes = []
	datamandatory = []
	datavalues = []
	datarows = []
	columns = 0
	for row in ext_rows:
		xrow += 1
		if xrow < row_start and xrow != row_labels:
			continue
		if row_stop and row_stop > 0 and xrow > row_stop:
			break
		tmp_list = []
		i = 0
		for cell in row:
			if isinstance(cell, six.string_types):
				if columns == 0: 
					tmp_list.append(cell.replace('"',''))
				else: tmp_list.append(cell.strip().replace('"','').encode('utf8'))
			else: tmp_list.append(cell)
			if newdata and columns > 0 and i <= columns :
				x = 0 
				if isinstance(cell, six.string_types): x = len(cell)
				lengths[i] = max( x, lengths[i])
				if datatypes[i] == "Data":
					if lengths[i] > 140:
						datatypes[i] = "Small Text"
					else:
						if isinstance(cell, int): datatypes[i] = "Int"
						if isinstance(cell, long): datatypes[i] = "Int"
						if isinstance(cell, float): datatypes[i] = "Float"
						if isinstance(cell, datetime): datatypes[i] = "Datetime"
						if isinstance(cell, date): datatypes[i] = "Date"
				else:
					if cell and cell != "" and cell != None and cell != 0 and cell != "0":
						if datatypes[i] == "Int" and not isinstance(cell, int) and not isinstance(cell, long): datatypes[i] = "Data"
						if datatypes[i] == "Float" and not isinstance(cell, float): datatypes[i] = "Data"
						if datatypes[i] == "Date" and not isinstance(cell, date): datatypes[i] = "Data"
						if datatypes[i] == "Datetime" and not isinstance(cell, datetime): datatypes[i] = "Data"
				if not cell or cell == "" or cell == None:
					if datamandatory[i] == 1: datamandatory[i] = 0
				if datatypes[i] == "Data" and datamandatory[i] == 1: 
					if not cell.strip() in datavalues[i]:
						datavalues[i].append(cell.strip())
			i += 1
		if xrow == row_labels:
			labels = tmp_list
			columns = len(labels)
			fields = tmp_list
			i = 1
			while i <= columns :
				lengths.append(0)
				datatypes.append("Data")
				datamandatory.append(1)
				datavalues.append([])
				j = i - 1
				fields[j] = str(fields[j]).lower().replace(" ", "_")
				i += 1
			datarows.append(fields)
		else:
			datarows.append(tmp_list)
	if newdata:
		i = 0
		for cell in labels:
			if datatypes[i] == "Data" and datamandatory[i] == 1 and len(datavalues[i]) <= 10:
				datatypes[i] = "Select"
				listdv = ""
				for dv in datavalues[i]:
					listdv = listdv + str(dv) + "\n"
				datavalues[i] = listdv
			else: 
				datavalues[i] = ""
			i += 1
		adddoctype(name, module, fields, labels, datatypes, datamandatory, datavalues)
	return datarows

def adddoctype(name, module, fields, labels, datatypes, datamandatory, datavalues, roles=None):
	if not frappe.db.exists('DocType', name):
		doc = frappe.get_doc({
			"doctype": "DocType",
			"module": module,
			"name": name,
			"quick_entry": 0,
			"custom": 1 })
		i = 0
		for cell in labels:
			doc_field = frappe.get_doc({
				"doctype": "DocField",
				"label": cell,
				"fieldtype": datatypes[i],
				"fieldname": fields[i],
				"reqd": datamandatory[i],
				"in_standard_filter": datamandatory[i] if i < 3 else 0,
				"search_index": datamandatory[i] if i < 3 and datatypes[i] != 'Small Text' else 0,
				"options": datavalues[i] if datatypes[i] == "Select" else "",
				"in_list_view": 1 if i  < 3 else 0})
			doc.append ("fields", doc_field)
			i += 1
			
		if roles == None:
			roles = ["System Manager", "Administrator"]
		for perm in roles:
			doc_perm = frappe.get_doc({
				"doctype": "DocPerm",
				"role": perm})
			doc.append ("permissions", doc_perm)
		doc.insert(ignore_permissions=True)

def addrecords(name, datarows, limit=65000):
	columns = 0
	j = 0
	for row in datarows:
		if j >= limit: break
		if columns == 0: 
			fields = row
			columns = len(fields)
			continue
		datadoc = {"doctype": name}
		i = 0
		for cell in row:
			if i >= columns: break
			datadoc.setdefault(fields[i], cell)
			i += 1
		doc = frappe.get_doc(datadoc)
		doc.insert(ignore_permissions=True)
		j += 1
	return j

