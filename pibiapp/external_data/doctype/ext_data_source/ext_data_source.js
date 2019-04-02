// Copyright (c) 2019, Dolores Juliana and contributors
// For license information, please see license.txt

frappe.ui.form.on('Ext Data Source', {
	refresh: function(frm) {
		frm.page.add_menu_item(__("Clean Data Loaded"), function() {
				if(frappe.confirm(__("This is PERMANENT action and you cannot undo. Continue?"),
					function() {
						return frappe.call({
							method: 'pibiapp.external_data.data_manage.deletedata',
							args: {
								doctype: frm.doc.name
							},
							callback: function() {
								frm.refresh();
							}
						});
					}));
			});
	}
});
