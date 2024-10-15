// Copyright (c) 2024, jignasha and contributors
// For license information, please see license.txt


frappe.ui.form.on('Employee Gratuity', {

    // Set the gratuity omponent
    onload: function(frm) {
        
        frm.messageShown = false;
        frm.previousEmployee = null; 

        frappe.db.get_value('Salary Component', {'name': 'Gratuity'},'name', (r) => {

            if(r.name){
                frm.set_value('salary_component', r.name); 
            }
            
        });
             
    },

    // Filter Salary Slip dropdown for employee
    refresh: function(frm){
        frm.set_query('last_salary_slip', function() {
            return {
                filters: {
                    'employee': cur_frm.doc.employee  
                }
            };
        });
    },
    employee: function(frm) {
        if (frm.doc.employee) {
            // Check if the employee has changed
            if (frm.previousEmployee !== frm.doc.employee) {
                frm.messageShown = false; // Reset the flag for the new employee
                frm.previousEmployee = frm.doc.employee;
            }

            // Perform the check and update fields if needed
            frappe.db.get_value('Employee', frm.doc.employee, 'relieving_date', (r) => {
                if (!r.relieving_date) {
                    // Show a message only if it hasn't been shown already
                    if (!frm.messageShown) {
                        let msg = frappe.msgprint({
                            title: 'Notice',
                            indicator: 'yellow',
                            message: 'The selected employee does not have a relieving date.'
                        });

                        // Set a timeout to hide the message after 1 second
                        setTimeout(() => {
                            msg.hide();
                        }, 1000); // 1 second

                        // Set the flag to true to indicate the message has been shown
                        frm.messageShown = true;
                    }

                    // Clear the total_years_of_experience field
                    frm.set_value('total_years_of_experience', '');
                } else {
                    // Reset the flag if relieving_date is available
                    frm.messageShown = false;

                    var a = frm.doc.date_of_joining;
                    var b = frm.doc.date_of_leaving;

                    // Function to format date as dd-mm-yyyy
                    function formatDate(dateString) {
                        var date = new Date(dateString);
                        var day = String(date.getDate()).padStart(2, '0');
                        var month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-based
                        var year = date.getFullYear();
                        return `${day}-${month}-${year}`;
                    }

                    // Function to calculate year difference as a float
                    function calculateYearDifference(date1, date2) {
                        var d1 = new Date(date1);
                        var d2 = new Date(date2);
                        var diffInMilliseconds = d2 - d1;
                        var diffInYears = diffInMilliseconds / (1000 * 60 * 60 * 24 * 365.25); // Considering leap years
                        return parseFloat(diffInYears.toFixed(1)); // Rounded to 1 decimal place
                    }

                    if (a && b) {
                        var formattedDateOfJoining = formatDate(a);
                        var formattedDateOfLeaving = formatDate(b);

                        // console.log(formattedDateOfJoining, formattedDateOfLeaving); // Log the formatted dates to the console

                        // Calculate the year difference
                        var yearDifference = calculateYearDifference(a, b);

                        // console.log(`Total years of experience: ${yearDifference}`); // Log the year difference

                        // Set the total_years_of_experience field with the year difference
                        frm.set_value('total_years_of_experience', yearDifference);
                    }
                }
            });
        } else {
            // Reset the flag when the employee field is cleared
            frm.messageShown = false;
            frm.previousEmployee = null; // Clear previous employee tracking
        }		
    },
    validate: function(frm) {
        // console.log('Validation Check');

        // Fetch the relieving_date from the Employee doctype and perform validation
        if (frm.doc.employee) {
            frappe.db.get_value('Employee', frm.doc.employee, 'relieving_date', (r) => {
                if (!r.relieving_date) {
                    // Show popup message if relieving_date does not exist
                    frappe.msgprint({
                        title: 'Notice',
                        indicator: 'red',
                        message: 'The selected employee does not have a relieving date. The form cannot be saved.'
                    });

                    // Set the total_years_of_experience field to an empty string
                    frm.set_value('total_years_of_experience', '');

                    // Prevent the form from being saved
                    frappe.validated = false;
                } else {
                    // Additional validation for total_years_of_experience
                    if (frm.doc.total_years_of_experience < 5) {
                        frappe.msgprint({
                            title: 'Notice',
                            indicator: 'red',
                            message: `Employee: ${frm.doc.employee} (${frm.doc.employee_name}) is not eligible for gratuity as they have not completed 5 working years.`
                        });

                        // Prevent the form from being saved
                        frappe.validated = false;
                    }
                }
            });
        }
    },
    last_salary_slip: function(frm){
        if (frm.doc.last_salary_slip){
            frappe.call({
                method: 'smk_hrms.smk_hrms.doctype.employee_gratuity.employee_gratuity.get_last_basic',
                args: {
                    last_salary_slip: frm.doc.last_salary_slip
                },
                callback: function (r) {
                    if (r.message) {
                        var last_basic = r.message
                        var total_years = frm.doc.total_years_of_experience;
                        
                        frm.set_value('last_basic', last_basic)
                        frm.refresh_field('last_basic')

                        if (total_years>5.0)
                        {
                            
                            var gratuity = (15 * last_basic * total_years) / 30;

                            frm.set_value('amount', gratuity);
                            frm.refresh_field('amount');
                        }
                        
                        
                    }
                }
            });
        }
    }
    
    
});
