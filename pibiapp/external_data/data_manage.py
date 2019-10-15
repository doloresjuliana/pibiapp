# -*- coding: utf-8 -*-
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
from frappe import _
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
from frappe.utils.csvutils import read_csv_content
import six
from six import text_type, string_types
from datetime import date, datetime
from frappe.utils import nowdate
from frappe.utils.dateutils import parse_date
from frappe.utils import cint, cstr, flt, getdate, get_datetime, get_url, get_url_to_form
from xml.etree import ElementTree as ET
import copy

def force_to_unicode(text):
	if text == None: text = " "
	resp = text.encode('ascii', 'ignore').decode('ascii')
	return resp

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
	tmp_list = []
	fields = []
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
		# Row empty?
		if columns > 0:
			rowempty = 1
			i = 0
			for cell in row:
				if i >= columns: break
				if cell and str(cell).strip() != "":
					rowempty = 0
					break
				i += 1
			if rowempty == 1: continue

		tmp_list = []
		i = 0
		for cell in row:
			# Label empty END
			if columns == 0 and (cell == None or cell == ""): break
			if columns > 0 and i >= columns: break

			if isinstance(cell, six.string_types):
				if columns == 0: 
					tmp_list.append(cell.replace('"','').replace('.','').replace(',',''))
				else: tmp_list.append(cell.strip().replace('"','').encode('utf8'))
			else: 
				tmp_list.append(cell)
			if newdata and columns > 0 and i <= columns :
				x = 0 
				if isinstance(cell, six.string_types): x = len(cell)
				lengths[i] = max( x, lengths[i])
				if datatypes[i] == "PTE":
					if lengths[i] > 140:
						datatypes[i] = "Small Text"
					else:
						if isinstance(cell, int): datatypes[i] = "Int"
						if isinstance(cell, long): datatypes[i] = "Int"
						if isinstance(cell, float): datatypes[i] = "Float"
						if isinstance(cell, datetime): datatypes[i] = "Datetime"
						if isinstance(cell, date): datatypes[i] = "Date"
						if isinstance(cell, str): datatypes[i] = "Data"
				else:
					if cell and cell != "" and cell != None and cell != 0 and cell != "0":
						if lengths[i] > 140: datatypes[i] = "Small Text"
						if datatypes[i] == "Int" and not isinstance(cell, int) and not isinstance(cell, long): datatypes[i] = "Data"
						if datatypes[i] == "Float" and not isinstance(cell, float): datatypes[i] = "Data"
						if datatypes[i] == "Date" and not isinstance(cell, date): datatypes[i] = "Data"
						if datatypes[i] == "Datetime" and not isinstance(cell, datetime): datatypes[i] = "Data"
				if not cell or cell == "" or cell == None:
					if datamandatory[i] == 1: datamandatory[i] = 0
				if datatypes[i] == "Data" and datamandatory[i] == 1 and isinstance(cell, str):
					if not cell.strip() in datavalues[i]:
						datavalues[i].append(cell.strip())
			i += 1
		if xrow == row_labels:
			fields = tmp_list
			columns = len(tmp_list)
			labels = copy.deepcopy(tmp_list)
			i = 1
			while i <= columns :
				lengths.append(0)
				datatypes.append("PTE")
				datamandatory.append(1)
				datavalues.append([])
				j = i - 1
				labels[j] = force_to_unicode(labels[j])
				fields[j] = force_to_unicode(fields[j])
				fields[j] = str(fields[j]).lower().replace(" ", "_")
				if fields[j] == "_":
					fields[j] = "column_" + str(i)
					labels[j] = "Column " + str(i)
				i += 1
			datarows.append(fields)
			# template diferent
			if not newdata:
                            meta = frappe.get_meta(name)
                            i = 1
                            while i <= columns :
                               j = i - 1
                               df = meta.get_field(fields[j])
                               if not df:
                                   frappe.throw(_("The fields of the file you are trying to load do not correspond to the fields in the initial template file"))
                               i += 1
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
			if datatypes[i] == "PTE": datatypes[i] = "Data"
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
				
		doc_field = frappe.get_doc({
				"doctype": "DocField",
				"label": "Row Original",
				"fieldtype": "Text Editor",
				"fieldname": "row_original",
				"reqd": 0,
				"in_standard_filter": 0,
				"search_index": 0,
				"options": "",
				"in_list_view": 0,
				"hidden": 1})
		doc.append ("fields", doc_field)
			
		if roles == None:
			roles = ["System Manager", "Administrator"]
		for perm in roles:
			doc_perm = frappe.get_doc({
				"doctype": "DocPerm",
				"role": perm})
			doc.append ("permissions", doc_perm)
		doc.insert(ignore_permissions=True)

def addrecords(name, datarows, limit=65000):
	meta = frappe.get_meta(name)
	columns = 0
	x = 0
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
			df = meta.get_field(fields[i])
			fieldtype = df.fieldtype if df else "Data"
			if fieldtype in ("Int", "Check"): 
				cell = cint(cell)
			elif fieldtype in ("Float", "Currency", "Percent"):
				cell = flt(cell)
			elif fieldtype == "Date":
				if cell and isinstance(cell, datetime):
					cell = str(cell)
				if cell and isinstance(cell, string_types): 
					cell = getdate(parse_date(cell))
			elif fieldtype == "Datetime":
				if cell:
					if " " in cell:
						_date, _time = cell.split()
					else:
						_date, _time = cell, '00:00:00'
					_date = parse_date(cell)
					cell = get_datetime(_date + " " + _time)
				else:
					cell = None
			elif fieldtype in ("Link", "Dynamic Link", "Data") and cell:
				cell = cstr(cell)

			datadoc.setdefault(fields[i], cell)
			i += 1

		row_original = str(datadoc)
		xduplicates = frappe.get_list(name, filters={'row_original': row_original}, fields=['name'])
		j += 1
		if len(xduplicates) > 0:
			x += 1
			continue
		datadoc = conversionrules(datadoc)
		datadoc.setdefault("row_original", row_original)
		doc = frappe.get_doc(datadoc)
		doc.insert(ignore_permissions=True)
	return j - x

def conversionrules(doc, conversion_type='During loading'):
	rules = frappe.get_all("Conversion Rules", 
		filters={"reference_doctype": doc['doctype'], "conversion_type": conversion_type}, 
		fields=["origin_field", "action", "receiver_field"],
		order_by = 'execution_order')
	for rule in rules:
		x = doc.get(rule.origin_field)
		y = executeaction(x, rule.action)
		if doc[rule.receiver_field]: doc[rule.receiver_field] = y
		else: doc.setdefault(rule.receiver_field, y)
	return doc

def executeaction(x, action, param1=None, param2=None):
	if not x or x == None: return x
	xact = ['Convert to Uppercase','Convert to Lowercase','Convert First Letter to Uppercase',
				'Remove White Character from Beginning and End','Replace character or string (All)',
				'Replace character or string (the First one)','Replace character or string (the Last one)']
	i = xact.index(action)
	if i == 0: return x.upper()
	if i == 1: return x.lower()
	if i == 2: return (x[0].upper() + x[1:].lower())
	if i == 3: return x.strip()
	if i == 4 and param1 != None and param2 != None: return x.replace(param1, param2)
	if i == 5 and param1 != None and param2 != None: return x.replace(param1, param2, 1)
	
	return x

def changedoctype(self, method=None):
	if not frappe.db.exists('DocType', self.reference_doctype):
		return
	if not frappe.db.table_exists(self.name) and not self.docfield:
		return
	allfields = frappe.get_list('Change DocField', filters={'parent': self.name}, fields="*")
	keydata = ["label","fieldtype","reqd","search_index","in_list_view","in_standard_filter","options","default","length","in_global_search","allow_in_quick_entry","bold","description"]
	for onefield in allfields:
		docname = frappe.get_list('DocField', 
			filters={'parent': self.reference_doctype, 'fieldname': onefield.fieldname }, 
			fields=["name"])
		doc = frappe.get_doc('DocField', docname[0]['name'])
		for onekey in keydata:
			if doc.get(onekey) != onefield.get(onekey):
				setattr(doc,onekey,onefield.get(onekey))
		doc.save()

def doctype_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	return frappe.db.sql("""select eds.name
		from `tabExt Data Source` eds
			INNER JOIN tabDocType dt on eds.name = dt.name
		""",{
				"today": nowdate(),
				"txt": "%%%s%%" % txt,
				"_txt": txt.replace("%", ""),
				"start": start,
				"page_len": page_len
			}, as_dict=as_dict)

@frappe.whitelist()
def deletedata(doctype):
	numrecords = frappe.db.count(doctype)
	if  not numrecords or numrecords == 0:
		frappe.throw(_("{0} is empty contains {1} records.").format(doctype,numrecords))
	if not frappe.db.exists('DocType', doctype):
		frappe.throw(_("{0} is not a doctype of the database.").format(doctype))
	if not frappe.db.exists('Ext Data Source', doctype):
		frappe.throw(_("{0} is not a External Data.").format(doctype))

	il = frappe.get_all(doctype, fields=['name'])
	failed = []
	i = 0
	for dd in il:
		d = dd.name
		try:
			frappe.delete_doc(doctype, d)
			if numrecords >= 5:
				frappe.publish_realtime("progress",
					dict(progress=[i+1, numrecords], title=_('Deleting {0}').format(doctype), description=d),
						user=frappe.session.user)
			i += 1
		except Exception:
			failed.append(d)

	message = str(numrecords - len(failed)) + ' records loaded in the DocType ' + doctype 
	frappe.publish_realtime('msgprint', message )
	return failed
