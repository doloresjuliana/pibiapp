# Copyright (c) 2018-2019, Dolores Juliana Fdez Martin
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
import frappe
from frappe import _
from frappe.utils import get_request_site_address
import requests
from json import dumps
from frappe.modules.utils import get_doctype_module, get_module_app
from frappe.desk.tags import DocTags
from pibiapp.nextcloud import nextcloud_apis
import json
import os
import time
import sys

class nextcloud_link():
	def __init__(self):
		self.isconnect = False
		docns = frappe.get_doc("Nextcloud Settings")
		if not docns or not docns.enable:
			return
		self.initialpath = docns.initial_path
		self.sharepublic = docns.share_public
		self.enabletagging = docns.enable_tagging
		self.relationaltagging = docns.relational_tagging
		self.url = docns.script_url
		self.lasttag = 0
		nem = frappe.get_all("Nextcloud Excluded Module", filters={ "parent": "Nextcloud Settings" }, fields=["excluded_module"], distinct=True)
		self.excludedmodules = [row.get("excluded_module") for row in nem]
		host = self.url + docns.webdav_path 
		username = docns.client_id
		passwd = docns.get_password(fieldname='client_secret',raise_exception=False)  
		# Conect
		self.webdav = nextcloud_apis.WebDav(host=host, username=username, password=passwd)		  
		self.ocs = nextcloud_apis.OCS(docns.script_url, docns.client_id, passwd, js=True)
		data_json  = self.ocs.getUsers()
		data_string = json.dumps(data_json)
		decoded = json.loads(data_string)
		if str(decoded["ocs"]["meta"]["status"]) == 'ok':
			self.isconnect = True
			
	def tagging(self, doc, idfile, relational):
		self.actualizetags()
		lista = self.listtags(doc, idfile, relational)
		for display_name in lista:
			self.puttag( display_name, idfile)
	
	def puttag(self, display_name, idfile):
		idtag = self.searchtag( display_name)
		if idtag == "0" or idtag == None:
			vstatus = self.webdav.addtag( display_name)
			self.actualizetags(search_name=display_name)
			idtag = self.searchtag( display_name)
			if idtag == "0" or idtag == None: return
		self.webdav.assingtag(idfile, idtag)

	def searchtag(self, display_name):
		idtag = frappe.get_value("Nextcloud Tags",{"display_name":display_name},"id_tag")
		if not idtag: idtag = "0"
		return idtag
		
	def actualizetags(self, spaces=1, search_name=""):
		docns = frappe.get_doc("Nextcloud Settings")
		if docns.last_id_tag is None or search_name != "": spaces = 50
		j = v = int(0)
		i = lastid = int(0 if docns.last_id_tag is None else docns.last_id_tag)
		while True:
			i += 1
			display_name = self.webdav.gettag(str(i))
			if display_name != "":
				lastid = i
				self.inserttag( i, display_name)	
				j += 1
				if display_name == search_name: break
				else: v = 0
			else:
				v += 1
				if (v >= spaces): break
			if (v > spaces ): break
		docns.last_id_tag = lastid
		docns.save()

	def inserttag(self, idtag, display_name):
		doctag = frappe.new_doc("Nextcloud Tags")
		doctag.update( {"id_tag" : idtag, "display_name" : display_name })
		doctag.insert()
	
	def relationaltags(self, doctype, name, idfile):
		docntrans = frappe.get_doc(doctype, name)
		meta = frappe.get_meta(doctype)
		lista = ""
		for lf in meta.get_link_fields():
			tag = docntrans.get(lf.fieldname)
			if tag != "" and tag != None:
				lista = lista + " # " + tag
		lista = lista + DocTags(doctype).get_tags(name).replace("," , " # ")
		return lista
				
	def deletetags(self, doc, idfile, relational=True):
		lista = self.listtags(doc, idfile, relational)
		status_code = self.webdav.deletetags(idfile, nodelete=lista)
		
	def listtags(self, doc, idfile, relational):
		doctype = doc.attached_to_doctype
		module = get_doctype_module(doctype)
		name = doc.attached_to_name 
		lista = doctype + " # " + module + " # " + name
		if relational: lista = lista + self.relationaltags(doctype, name, idfile)
		return lista.split(" # ")
					
	def shareModule(self, doc):
		# add group for module 
		data_json = doc.nc.ocs.getGroup(doc.nc.module)
		data_string = json.dumps(data_json)
		decoded = json.loads(data_string)
		isgroup = str(decoded["ocs"]["meta"]["statuscode"])
		if isgroup == '404':
			data_json = doc.nc.ocs.addGroup(doc.nc.module)
		# add Share group in Nextcloud
		shareType = 1
		permit = 1
		data_json  = doc.nc.ocs.createShare(doc.nc.pathglobal,shareType,shareWith=doc.nc.module,publicUpload=True,password=None,permissions=permit)
		return data_json
		

@frappe.whitelist()
def nextcloud_before_insert(doc, method=None):
	doc.flags.ignore_nc = True
	nc = nextcloud_link()
	if not nc.isconnect: return
	doc.flags.ignore_file_validate = True
	doctype = doc.attached_to_doctype
	module = get_doctype_module(doctype)
	# Excluded module
	if module in nc.excludedmodules: return
	# File previously attached to another transaction
	if not doc.file_name or doc.file_name == None: return
	if " NC/f/" in doc.file_name: return
	doc.flags.ignore_nc = False
	site = frappe.local.site
	if doc.is_private: local_fileobj = "./" + site + doc.file_url
	else: local_fileobj = "./" + site + "/public" + doc.file_url
	fileobj = local_fileobj.split('/')
	uu = len(fileobj) - 1
	doc.nc = nc
	doc.nc.module = module
	doc.nc.app = get_module_app(module)
	doc.nc.path = nc.initialpath + "/" + doc.nc.app + "/" + module + "/" + doctype
	doc.nc.pathglobal = doc.nc.path + "/" + fileobj[uu].encode("ascii", "ignore").decode("ascii")
	doc.nc.local_fileobj = local_fileobj
	doc.nc.remote_fileobj=fileobj[uu].encode("ascii", "ignore").decode("ascii")
	

@frappe.whitelist()
def nextcloud_insert(doc, method=None):
	if doc.flags.ignore_nc: return
	# upload to nextcloud
	if not "http" in doc.nc.local_fileobj:
		doc.nc.webdav.upload(local_fileobj=doc.nc.local_fileobj, remote_fileobj=doc.nc.remote_fileobj, nc_path=doc.nc.path)
	else:
		data = frappe.db.get_value("File", {"file_url": doc.file_url , "file_name": ["like", "%NC/f/%"]}, ["attached_to_doctype", "name", "file_name"], as_dict=True)
		if data:
			if  doc.attached_to_doctype != data.attached_to_doctype:
				doctype = data.attached_to_doctype
				module = get_doctype_module(doctype)
				app = get_module_app(module)
				doc.nc.pathglobal = doc.nc.initialpath + "/" + app + "/" + module + "/" + doctype + "/" + doc.file_name
				data_json = doc.nc.shareModule(doc)
			fname = data.file_name.replace(" NC/f/","#")
			doc.file_name = fname.split("#")[0] + " NC(" + data.name + ")/f/" + fname.split("#")[1]
			doc.save()
		return
	data_json  = doc.nc.shareModule(doc)
	# add public Share in Nextcloud
	if doc.nc.sharepublic or doc.is_private == False:
		shareType = 3
		data_json  = doc.nc.ocs.createShare(doc.nc.pathglobal,shareType)
		if data_json == "":
			time.sleep(2)
			data_json  = doc.nc.ocs.createShare(doc.nc.pathglobal,shareType)
	data_string = json.dumps(data_json)
	decoded = json.loads(data_string)
	try:
		fileid = str(decoded["ocs"]["data"]["file_source"]) 
	except TypeError:
		fname = frappe.db.get_value("File", {"file_name": ["like", doc.file_name + " NC/f/%"]}, "name")
		docorigin = frappe.get_doc('File', str(fname))
		if docorigin:
			docorigin.content_hash = doc.content_hash
			docorigin.flags.ignore_file_validate = True
			docorigin.save()
			if doc.nc.enabletagging:
				fileid = str(docorigin.file_name.replace(" NC/f/","#").split("#")[1])
				doc.nc.deletetags(docorigin, fileid, relational=doc.nc.relationaltagging)
				doc.nc.tagging(docorigin, fileid, relational=doc.nc.relationaltagging)
			os.remove(doc.nc.local_fileobj)
			doc.delete()
			frappe.db.commit()
		sys.exit()
	if doc.nc.sharepublic or doc.is_private == False:
		urllink = str(decoded["ocs"]["data"]["url"]) 
	else:
		urllink = doc.nc.url + "/f/" + fileid
	# update doctype file
	if urllink != None and urllink != "":
		doc.file_url = urllink
		doc.file_name = doc.file_name.encode("ascii", "ignore").decode("ascii") + " NC/f/" + fileid
		doc.save()
    	# delete local file
	os.remove(doc.nc.local_fileobj)
	# tagging
	if doc.nc.enabletagging: doc.nc.tagging(doc, fileid, relational=doc.nc.relationaltagging)
	
@frappe.whitelist()
def nextcloud_before_delete(doc, method=None):
	doc.flags.ignore_nc = True
	nc = nextcloud_link()
	if not nc.isconnect: return
	doc.flags.ignore_file_validate = True
	doctype = doc.attached_to_doctype
	module = get_doctype_module(doctype)
	# Excluded module
	if module in nc.excludedmodules: return
	# File previously attached to another transaction
	if not doc.file_name or doc.file_name == None: return
	if not " NC/f/" in doc.file_name: return
	doc.flags.ignore_nc = False
	data = frappe.db.get_value("File", {"file_url": doc.file_url , "file_name": ["like", "%NC(%"]}, ["attached_to_doctype", "attached_to_name"], as_dict=True)
	if data:
		frappe.throw(_("The file can not be deleted while it is related to this transaction: {0} {1}").format(data.attached_to_doctype, data.attached_to_name))

@frappe.whitelist()
def nextcloud_delete(doc, method=None):
	if doc.flags.ignore_nc: return
	nc = nextcloud_link()
	if not nc.isconnect: return
	doctype = doc.attached_to_doctype
	module = get_doctype_module(doctype)
	if module in nc.excludedmodules: return
	ncf = doc.file_name.find(" NC/f/")
	if ncf == -1: return
	filename = doc.file_name[0:ncf]
	app = get_module_app(module)
	path = nc.initialpath + "/" + app + "/" + module + "/" + doctype + "/" + filename
	nc.webdav.delete(path)	
			
@frappe.whitelist()
def nextcloud_callback(code=None):
	nc = nextcloud_link()
	if nc.isconnect == True:
		mensaje = 'Correct access to Nextcloud'
	else:
		mensaje = 'ERROR. Incorrect access'  
	frappe.throw(_(mensaje))
