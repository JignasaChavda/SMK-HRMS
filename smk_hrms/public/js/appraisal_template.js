frappe.ui.form.on("Appraisal Template", {
    validate: function(frm) {
        // Validation 1: Check weightage totals for each KRA in rating_criteria
        if (frm.doc.rating_criteria && frm.doc.rating_criteria.length > 0) {
            let kra_totals = {};
            let errors = [];
            
            // Group by KRA and calculate totals
            frm.doc.rating_criteria.forEach(row => {
                if (!row.custom_kra || row.custom_kra.trim() === "") {
                    return; // Skip rows without KRA
                }
                
                let weightage = parseFloat(row.per_weightage);
                if (isNaN(weightage)) {
                    return; // Skip rows with invalid weightage
                }
                
                kra_totals[row.custom_kra] = (kra_totals[row.custom_kra] || 0) + weightage;
            });

            // Check each KRA total and collect errors
            Object.keys(kra_totals).forEach(kra => {
                let total = Math.round(kra_totals[kra] * 100) / 100;
                if (Math.abs(total - 100) > 0.01) { // Allow small rounding error
                    // Find all rows for this KRA to show row numbers
                    let rowNumbers = [];
                    frm.doc.rating_criteria.forEach((row, index) => {
                        if (row.custom_kra === kra) {
                            rowNumbers.push(index + 1);
                        }
                    });
                    
                    errors.push(`KRA "${kra}" total weightage is ${total}% (must be 100%) - Check rows: ${rowNumbers.join(', ')}`);
                }
            });

            if (errors.length > 0) {
                frappe.throw([
                    '<b>Weightage Validation Failed:</b>',
                    'Each KRA must have a total weightage of exactly 100%',
                    ...errors
                ].join('<br>'));
            }
        }
        
        // Validation 2: Only check KRA presence if weightage validation passed
        // Check if all KRAs from goals table are present in rating_criteria
        if (frm.doc.goals && frm.doc.goals.length > 0) {
            let goals_kras = new Set();
            let rating_kras = new Set();
            
            // Collect unique KRAs from goals table
            frm.doc.goals.forEach(row => {
                if (row.key_result_area && row.key_result_area.trim() !== "") {
                    goals_kras.add(row.key_result_area.trim());
                }
            });
            
            // Collect unique KRAs from rating_criteria table
            if (frm.doc.rating_criteria && frm.doc.rating_criteria.length > 0) {
                frm.doc.rating_criteria.forEach(row => {
                    if (row.custom_kra && row.custom_kra.trim() !== "") {
                        rating_kras.add(row.custom_kra.trim());
                    }
                });
            }
            
            // Find KRAs in goals that are missing in rating_criteria
            let missing_kras = [];
            goals_kras.forEach(kra => {
                if (!rating_kras.has(kra)) {
                    missing_kras.push(kra);
                }
            });
            
            if (missing_kras.length > 0) {
                frappe.throw([
                    '<b>Missing KRAs in Rating Criteria:</b>',
                    `The following KRAs from Goals table are not found in Rating Criteria:`,
                    `<b>"${missing_kras.join('", "')}"</b>`,
                    'Please add these KRAs to the Rating Criteria table with proper weightage distribution.'
                ].join('<br>'));
            }
        }
    }
});