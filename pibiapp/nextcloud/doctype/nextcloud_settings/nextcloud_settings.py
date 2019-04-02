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
import frappe
import os
from frappe.model.document import Document
from frappe import _
from frappe.utils.backups import new_backup
from frappe.utils.background_jobs import enqueue
from pibiapp.nextcloud.nextcloud_link import nextcloud_callback, nextcloud_backup
from rq.timeouts import JobTimeoutException
from frappe.utils import (cint, split_emails, get_request_site_address,
	get_files_path, get_backups_path, get_url, encode)
from six import text_type, PY2


class NextcloudSettings(Document):
	def validate(self):
		if self.enable:
			if (not self.client_id or self.client_id == "" 
				or not self.client_secret or self.client_secret == "" 
				or not self.script_url or self.script_url == "" 
				or not self.webdav_path or self.webdav_path == ""):
				frappe.throw(_('If Nexcloud is enabled, the data is mandatory: Client id, Client Secret, Script Url and Webdav Path'))
			if self.enabled_nexcloud_upload:
				if (not self.send_notifications_to or self.send_notifications_to == "" 
					or not self.backup_frequency or self.backup_frequency == ""):
					frappe.throw(_('If Nexcloud Backups is enabled, the data is mandatory: Send Notifications To, Backup Frequency'))

@frappe.whitelist()
def take_backup():
	enqueue("pibiapp.nextcloud.doctype.nextcloud_settings.nextcloud_settings.take_backup_to_nextcloud", queue='long', timeout=1500)
	frappe.msgprint(_("Queued for backup. It may take a few minutes to an hour."))

def take_backups_daily():
	take_backups_if("Daily")

def take_backups_weekly():
	take_backups_if("Weekly")

def take_backups_if(freq):
	if frappe.db.get_value("Nextcloud Settings", None, "backup_frequency") == freq:
		take_backup_to_nextcloud()

def take_backup_to_nextcloud(retry_count=0, upload_db_backup=True):
	did_not_upload, error_log = [], []
	nc = frappe.db.get_value("Nextcloud Settings", None, "enable")
	ncb = frappe.db.get_value("Nextcloud Settings", None, "enabled_nexcloud_upload")
	try:
		if nc == "1" and ncb == "1":
			ncbf = frappe.db.get_value("Nextcloud Settings", None, "file_backup")
			ignore_files = False if ncbf else True
			did_not_upload, error_log = backup_to_nextcloud(upload_db_backup, ignore_files)
			if did_not_upload: raise Exception
			send_email(True, "Nextcloud")
	except JobTimeoutException:
		if retry_count < 2:
			args = {
				"retry_count": retry_count + 1,
				"upload_db_backup": False #considering till worker timeout db backup is uploaded
			}
			enqueue("pibiapp.nextcloud.doctype.nextcloud_settings.nextcloud_settings.take_backup_to_nextcloud",
				queue='long', timeout=1500, **args)
	except Exception:
		file_and_error = [" - ".join(f) for f in zip(did_not_upload, error_log)]
		error_message = ("\n".join(file_and_error) + "\n" + frappe.get_traceback())
		frappe.errprint(error_message)
		send_email(False, "Nextcloud", error_message)

def send_email(success, service_name, error_status=None):
	if success:
		if frappe.db.get_value("Nextcloud Settings", None, "send_email_for_successful_backup") == '0':
			return

		subject = "Backup Upload Successful"
		message ="""<h3>Backup Uploaded Successfully</h3><p>Hi there, this is just to inform you
		that your backup was successfully uploaded to your %s account. So relax!</p>
		""" % service_name

	else:
		subject = "[Warning] Backup Upload Failed"
		message ="""<h3>Backup Upload Failed</h3><p>Oops, your automated backup to %s
		failed.</p>
		<p>Error message: <br>
		<pre><code>%s</code></pre>
		</p>
		<p>Please contact your system manager for more information.</p>
		""" % (service_name, error_status)

	if not frappe.db:
		frappe.connect()

	recipients = split_emails(frappe.db.get_value("Nextcloud Settings", None, "send_notifications_to"))
	frappe.sendmail(recipients=recipients, subject=subject, message=message)

def backup_to_nextcloud(upload_db_backup=True, ignore_files=True):
	if not frappe.db:
		frappe.connect()
	respnc = ""
	if upload_db_backup:
		backup = new_backup(ignore_files=ignore_files)
		filebackup = os.path.join(get_backups_path(), os.path.basename(backup.backup_path_db))
		respnc = filebackup_upload(filebackup)
		# file backup
		if not ignore_files and not "Error" in respnc:
			filebackup = os.path.join(get_backups_path(), os.path.basename(backup.backup_path_files))
			respncf = filebackup_upload(filebackup)
			filebackup = os.path.join(get_backups_path(), os.path.basename(backup.backup_path_private_files))
			respncf = filebackup_upload(filebackup)
	did_not_upload = []
	if "Error" in respnc: error_log = [respnc]
	else: error_log = []
	return did_not_upload, list(set(error_log))

def filebackup_upload(filebackup):
	fname = filebackup.split("/backups/")[1]
	doc = frappe.get_doc({"doctype":"File", 
		"attached_to_doctype": "Nextcloud Settings", 
		"attached_to_name": "Nextcloud Settings",
		"is_folder": 0, "is_private": 1, 
		"name": fname, "file_name": fname,
		"file_url": filebackup})
	return nextcloud_backup(doc=doc)
