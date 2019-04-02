// Copyright (c) 2019, Dolores Juliana and contributors
// For license information, please see license.txt

frappe.ui.form.on('Change DocType Empty', {
	setup: function(frm) {
		frm.set_query("reference_doctype", function() {
			return{
				query: "pibiapp.external_data.data_manage.doctype_query"
			};
		});
	},
	refresh: function(frm) {
		var i;
		var x = document.querySelectorAll('button.btn.btn-xs.btn-default.grid-add-row');
		for (i = 0; i < x.length; i++) { x[i].style.display = 'none'; }
		x = document.querySelectorAll('button.btn.btn-xs.btn-danger.grid-remove-rows');
		for (i = 0; i < x.length; i++) {
			x[i].style.display = 'none';
			x[i].disabled = true;
		}
		x = document.querySelectorAll('button.btn.btn-default.btn-xs.pull-right.grid-insert-row');
		for (i = 0; i < x.length; i++) {
			x[i].remove();
		}
	}
});
