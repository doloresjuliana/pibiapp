// Copyright (c) 2019, Dolores Juliana and contributors
// For license information, please see license.txt

frappe.ui.form.on('Redash Business Intelligence', {
	refresh: function(frm) {
		var menuglobal;
		frm.disable_save();
		frm.page.clear_menu();
		frappe.call({
			method: "pibiapp.redash.doctype.redash_business_intelligence.redash_business_intelligence.get_dashboard",
			callback: function(r) {
				menuglobal = r.message;
				document.getElementById('embedredash').src = menuglobal[0][1];
				var x = menuglobal.length;
				var i;
				for (i = 0; i < x; i++) {
					var myUrl = new URL(menuglobal[i][1]);
					frm.page.add_menu_item(__(String(i + 1) + "- " + menuglobal[i][0]), function() {
						var str = this.text;
						var j = Number(str.substr(0, str.indexOf("-")));
						j = j - 1;
						document.getElementById('embedredash').src = menuglobal[j][1];
					});
				}
			}
		});
	}
});
