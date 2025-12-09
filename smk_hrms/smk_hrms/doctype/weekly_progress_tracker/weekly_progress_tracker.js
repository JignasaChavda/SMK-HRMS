// Copyright (c) 2025, jignasha and contributors
// For license information, please see license.txt

frappe.ui.form.on("Weekly Progress Tracker", {

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
                                    child.kra = row.custom_kra;  
                                    child.kpi = row.criteria;  
                                });

                                frm.refresh_field("kra_kpi_details");
                                // frm.save();

                            });
                    });
            });
    },

    // Add validation for the entire form
    validate: function(frm) {
        // Validate progress field in kra_kpi_details child table
        if (frm.doc.kra_kpi_details && frm.doc.kra_kpi_details.length > 0) {
            let errors = [];
            
            frm.doc.kra_kpi_details.forEach((row, index) => {
                if (row.progress !== null && row.progress !== undefined) {
                    let progress = parseFloat(row.progress);
                    
                    if (isNaN(progress)) {
                        errors.push(`Row ${index + 1}: Progress must be a number`);
                    } else if (progress < 0) {
                        errors.push(`Row ${index + 1}: Progress cannot be less than 0% (Current: ${progress}%)`);
                    } else if (progress > 100) {
                        errors.push(`Row ${index + 1}: Progress cannot exceed 100% (Current: ${progress}%)`);
                    }
                }
            });
            
            if (errors.length > 0) {
                frappe.throw([
                    '<b>Progress Validation Failed:</b>',
                    ...errors,
                    'Please correct the progress values before saving.'
                ].join('<br>'));
            }
        }
    },


    week_from_date(frm) {
        frm.trigger("set_week_to_date");
    },
    
    set_week_to_date(frm) {
        if (!frm.doc.week_from_date) return;

        // Convert string date to moment object
        let from_date = moment(frm.doc.week_from_date);

        // Add 6 days (1st day + 6 = 7th day)
        let to_date = from_date.add(6, "days").format("YYYY-MM-DD");

        // Set value
        frm.set_value("week_to_date", to_date);
    }
});
// Simple client-side validation while typing
// frappe.ui.form.on("KRA-KPI Details", {
//     progress: function(frm, cdt, cdn) {
//         let row = frappe.get_doc(cdt, cdn);
        
//         if (row.progress !== null && row.progress !== undefined) {
//             let progress = parseFloat(row.progress);
            
//             if (!isNaN(progress)) {
//                 if (progress > 100) {
//                     frappe.model.set_value(cdt, cdn, 'progress', 100);
//                     frappe.show_alert({
//                         message: __('Progress capped at 100%'),
//                         indicator: 'red'
//                     });
//                 } else if (progress < 0) {
//                     frappe.model.set_value(cdt, cdn, 'progress', 0);
//                     frappe.show_alert({
//                         message: __('Progress cannot be less than 0%'),
//                         indicator: 'red'
//                     });
//                 }
//             }
//         }
//     }
// });

