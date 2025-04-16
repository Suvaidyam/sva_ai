// Copyright (c) 2025, Suvaidyam and contributors
// For license information, please see license.txt

frappe.ui.form.on("SVA View Manager", {
    onload: function (frm) {
        frm.get_field("sql_output").html("");
    },
    refresh(frm) {
        // frm.disable_save();
        frm.add_custom_button(__("Execute"), ($btn) => {
            return frm
                .execute_action("Execute")
                .then(() => frm.trigger("render_sql_output"))
        });
        if (frm.doc.output && !frm.doc.__islocal){
            frm.add_custom_button(__('Fetch Columns'), async () => {
                await frappe.call("sva_ai.sva_ai.doctype.sva_view_manager.sva_view_manager.get_sql_columns", {
                    doc_name: frm.doc.name
                }).then((r) => {
                    if (r.message) {
                        frappe.show_alert({
                            message: __(r.message),
                            indicator: 'green'
                        });
                        refresh_field("columns");
                    }
                });
            })
        } else {
            frm.remove_custom_button(__('Fetch Columns'));
        }
        
    },

    render_sql_output: function (frm) {
        if (frm.sql_output) {
            frm.sql_output.destroy();
            frm.get_field("sql_output").html("");
        }

        try {
            let result = JSON.parse(frm.doc.output);
            frm.set_value("output", `${result.length} ${result.length == 1 ? "row" : "rows"}`);

            if (result.length) {
                let columns = Object.keys(result[0]);
                frm.sql_output = new DataTable(frm.get_field("sql_output").$wrapper.get(0), {
                    columns,
                    data: result,
                });
            }
        } catch (err) {
            console.log(err, 'error');
            frm.set_value("sql_output", err);
            frm.get_field("sql_output").html(`<pre style="color:red;">${frappe.utils.escape_html(frm.doc.sql_output)}</pre>`);
        }
    },

});
