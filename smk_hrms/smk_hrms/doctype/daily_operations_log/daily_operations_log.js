// Copyright (c) 2025, jignasha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daily Operations Log", {

    employee: function(frm) {

        if (!frm.doc.employee) return;

        // 1. Get designation from Employee
        frappe.db.get_value("Employee", frm.doc.employee, "designation")
            .then(r => {
                let designation = r.message.designation;

                if (!designation) {
                    frappe.msgprint("Designation not found for selected Employee.");
                    return;
                }

                // 2. Get Appraisal Template from Designation
                frappe.db.get_value("Designation", designation, "appraisal_template")
                    .then(d => {
                        let template = d.message.appraisal_template;

                        if (!template) {
                            frappe.msgprint("No Appraisal Template found in this Designation.");
                            return;
                        }

                        // 3. Load Appraisal Template document
                        frappe.db.get_doc("Appraisal Template", template)
                            .then(doc => {

                                // Child table for rating criteria
                                let criteria_list = doc.rating_criteria;

                                if (!criteria_list || criteria_list.length === 0) {
                                    frappe.msgprint("No Rating Criteria found in Appraisal Template.");
                                    return;
                                }

                                // Clear existing KRA-KPI rows
                                frm.clear_table("kra_kpi_details");

                                // 4. Add data in child table
                                criteria_list.forEach(row => {
                                    let child = frm.add_child("kra_kpi_details");
                                    child.kra = row.custom_kra;   // Map custom_kra → kra
                                    child.kpi = row.criteria;     // Map criteria → kpi
                                });

                                frm.refresh_field("kra_kpi_details");
                            });
                    });
            });
    },

    // auto-run when opening form if employee already selected
    // refresh(frm) {
    //     if (frm.doc.employee) {
    //         frm.trigger("employee");
    //     }
    // }
});
