# Copyright (c) 2018, Dolores Juliana Fdez Martin
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
from pibiapp.nextcloud import nextcloud_apis
import json
import os
import time

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
		doctype = doc.attached_to_doctype
		module = get_doctype_module(doctype)
		name = doc.attached_to_name 
		self.puttag( doctype, idfile)
		self.puttag( module, idfile)
		self.puttag( name, idfile)
		if relational: self.relationaltags(doctype, name, idfile)
	
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
		for lf in meta.get_link_fields():
			name = docntrans.get(lf.fieldname)
			if name != "" and name != None:
				self.puttag( name, idfile)		

@frappe.whitelist()
def nextcloud_insert(doc, method=None):
	nc = nextcloud_link()
	if not nc.isconnect: return
	doctype = doc.attached_to_doctype
	module = get_doctype_module(doctype)
	# Excluded module
	if module in nc.excludedmodules: return
	site = frappe.local.site
	local_fileobj = "./" + site + doc.file_url
	fileobj = local_fileobj.split('/')
	uu = len(fileobj) - 1
	# get path
	app = get_module_app(module)
	path = nc.initialpath + "/" + app + "/" + module + "/" + doctype
	pathglobal = path + "/" + fileobj[uu]
	# upload to nextcloud
	nc.webdav.upload(local_fileobj, remote_fileobj=fileobj[uu], nc_path=path)
	# add group for module 
	data_json = nc.ocs.getGroup(module)
	data_string = json.dumps(data_json)
	decoded = json.loads(data_string)
	isgroup = str(decoded["ocs"]["meta"]["statuscode"])
	if isgroup == '404':
		data_json = nc.ocs.addGroup(module)
	# add Share group in Nextcloud	
	shareType = 1
	permit = 1
	data_json  = nc.ocs.createShare(pathglobal,shareType,shareWith=module,publicUpload=True,password=None,permissions=permit)
	# add public Share in Nextcloud
	if nc.sharepublic:
		shareType = 3
		data_json  = nc.ocs.createShare(pathglobal,shareType)
		if data_json == "":
			time.sleep(2)
			data_json  = nc.ocs.createShare(pathglobal,shareType)
	data_string = json.dumps(data_json)
	decoded = json.loads(data_string)
	fileid = str(decoded["ocs"]["data"]["file_source"]) 
	if nc.sharepublic:
		urllink = str(decoded["ocs"]["data"]["url"]) 
	else:
		urllink = nc.url + "/f/" + fileid
	# update doctype file
	if urllink != None and urllink != "":
		doc.file_url = urllink
		doc.file_name = doc.file_name + " NC/f/" + fileid
		doc.save()
    # delete local file		
	os.remove(local_fileobj)
	# tagging
	if nc.enabletagging: nc.tagging(doc, fileid, relational=nc.relationaltagging)
	

@frappe.whitelist()
def nextcloud_delete(doc, method=None):
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
