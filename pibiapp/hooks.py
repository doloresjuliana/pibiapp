# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "pibiapp"
app_title = "App Pibi"
app_publisher = "Dolores Juliana"
app_description = "Application on the Frappe framework composed of modules that integrate the Frappe attachments with Nextcloud and will extend the functionality of ERPnext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "doloresjuliana@yahoo.es"
app_license = "GNU General Public License v3"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pibiapp/css/pibiapp.css"
# app_include_js = "/assets/pibiapp/js/pibiapp.js"

# include js, css files in header of web template
# web_include_css = "/assets/pibiapp/css/pibiapp.css"
# web_include_js = "/assets/pibiapp/js/pibiapp.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "pibiapp.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "pibiapp.install.before_install"
# after_install = "pibiapp.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pibiapp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
 	"File": {
  		"before_insert": "pibiapp.nextcloud.nextcloud_link.nextcloud_before_insert",
 		"after_insert": "pibiapp.nextcloud.nextcloud_link.nextcloud_insert",
 		"on_trash": "pibiapp.nextcloud.nextcloud_link.nextcloud_before_delete",
 		"after_delete": "pibiapp.nextcloud.nextcloud_link.nextcloud_delete"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pibiapp.tasks.all"
# 	],
# 	"daily": [
# 		"pibiapp.tasks.daily"
# 	],
# 	"hourly": [
# 		"pibiapp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pibiapp.tasks.weekly"
# 	]
# 	"monthly": [
# 		"pibiapp.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "pibiapp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pibiapp.event.get_events"
# }

