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
		self.url = docns.script_url
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
