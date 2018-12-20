// Copyright (c) 2018, Pibico
// For license information, please see license.txt

frappe.ui.form.on('Nextcloud Settings', {
	refresh: function(frm) {
		frm.clear_custom_buttons();
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
	}
});
