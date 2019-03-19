// Copyright (c) 2019, Dolores Juliana and contributors
// For license information, please see license.txt

frappe.ui.form.on('Successive loads', {
	refresh: function(frm) {
		cur_frm.add_fetch('reference_doctype', 'module', 'module');
		cur_frm.add_fetch('reference_doctype', 'data_format', 'data_format');
		cur_frm.add_fetch('reference_doctype', 'row_labels', 'row_labels');
		cur_frm.add_fetch('reference_doctype', 'row_start', 'row_start');

	}
});
