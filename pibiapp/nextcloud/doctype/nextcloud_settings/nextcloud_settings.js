// Copyright (c) 2018-2019, Pibico
// For license information, please see license.txt

frappe.ui.form.on('Nextcloud Settings', {
	refresh: function(frm) {
		frm.clear_custom_buttons();
		frm.events.take_backup(frm);
	},

	allow_nextcloud_access: function(frm) {
		if (frm.doc.client_id && frm.doc.client_secret) {
			frappe.call({
				method: "pibiapp.nextcloud.nextcloud_link.nextcloud_callback",
				callback: function(r) {
					if(!r.exc) {
						frm.save();
						window.open(r.message.url);
					}
				}
			});
		}
		else {
			frappe.msgprint(__("Please enter values for Nextcloud Access Key and Nextcloud Access Secret"))
		}
	},
	take_backup: function(frm) {
		if (frm.doc.enable && frm.doc.enabled_nexcloud_upload && frm.doc.backup_frequency){
			frm.add_custom_button(__("Take Backup Now"), function(frm){
				frappe.call({
					method: "pibiapp.nextcloud.doctype.nextcloud_settings.nextcloud_settings.take_backup",
					freeze: true
				})
			}).addClass("btn-primary")
		}
	}
});
