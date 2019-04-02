// Copyright (c) 2019, Dolores Juliana and contributors
// For license information, please see license.txt

frappe.ui.form.on('Conversion Rules', {
	setup: function(frm) {
		frm.set_query("reference_doctype", function() {
			return{
				query: "pibiapp.external_data.data_manage.doctype_query"
			};
		});
	},
	reference_doctype: function(frm) {
		if(!frm.doc.reference_doctype) return;

		frappe.model.with_doctype(frm.doc.reference_doctype, function() {
			var options = $.map(frappe.get_meta(frm.doc.reference_doctype).fields,
				function(d) {
					if(d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype)===-1) {
						return d.fieldname;
					}
					return null;
				}
			);
			frm.set_df_property('origin_field', 'options', options);
			frm.set_df_property('field_for_action', 'options', options);
		});
		var nn = 10;
		frm.set_value('execution_order', nn);
		frappe.model.get_value('Conversion Rules', {'reference_doctype': frm.doc.reference_doctype}, 'execution_order', function(d) {
    			nn = d.execution_order;
			nn += 10;
			frm.set_value('execution_order', nn);
  		});
		refresh_field('execution_order');
	},
	origin_field: function(frm) {
		if(!frm.doc.origin_field) return;
		var cact = ['Convert to Uppercase','Convert to Lowercase','Convert First Letter to Uppercase',
				'Remove White Character from Beginning and End','Replace character or string (All)',
				'Replace character or string (the First one)','Replace character or string (the Last one)',
				'If it is empty fill with a fixed value','Add a fixed value at the start',
				'Add a fixed value at the end','Concatenate another field at the beginning',
				'Concatenate another field at the end'];
		frappe.model.with_doctype(frm.doc.reference_doctype, function() {
			var options = $.map(frappe.get_meta(frm.doc.reference_doctype).fields,
				function(d) {
					if(d.fieldname && d.fieldname==frm.doc.origin_field) {
						return d.fieldtype;
					}
					return null;
				}
			);
			frm.set_value('type', options[0]); 
			refresh_field('type');
		});
		var xact = [];
		if(frm.doc.type != 'Int' && frm.doc.type != 'Float') { 
			xact = cact;
		}
		frm.set_df_property('action', 'options', xact);
		frm.set_df_property('receiver_field', 'options', [frm.doc.origin_field, 'Create new field']);
		frm.set_value('receiver_field', frm.doc.origin_field);
	},
	refresh: function(frm) {
		var cact = ['Convert to Uppercase','Convert to Lowercase','Convert First Letter to Uppercase',
				'Remove White Character from Beginning and End','Replace character or string (All)',
				'Replace character or string (the First one)','Replace character or string (the Last one)',
				'If it is empty fill with a fixed value','Add a fixed value at the start',
				'Add a fixed value at the end','Concatenate another field at the beginning',
				'Concatenate another field at the end'];
		if(frm.doc.reference_doctype) {
			frappe.model.with_doctype(frm.doc.reference_doctype, function() {
			var options = $.map(frappe.get_meta(frm.doc.reference_doctype).fields,
				function(d) {
					if(d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype)===-1) {
						return d.fieldname;
					}
					return null;
				}
			);
			frm.set_df_property('origin_field', 'options', options);
			frm.set_df_property('field_for_action', 'options', options);
			});
		}
		if(frm.doc.origin_field) {
			frappe.model.with_doctype(frm.doc.reference_doctype, function() {
			var options = $.map(frappe.get_meta(frm.doc.reference_doctype).fields,
				function(d) {
					if(d.fieldname && d.fieldname==frm.doc.origin_field) {
						return d.fieldtype;
					}
					return null;
				}
			);
			frm.set_value('type', options[0]); 
			refresh_field('type');
			});
			var xact = [];
			if(frm.doc.type != 'Int' && frm.doc.type != 'Float') { 
				xact = cact;
			}
			frm.set_df_property('action', 'options', xact);
			frm.set_df_property('receiver_field', 'options', [frm.doc.origin_field, 'Create new field']);
			frm.set_value('receiver_field', frm.doc.origin_field);
		}
	}
});
