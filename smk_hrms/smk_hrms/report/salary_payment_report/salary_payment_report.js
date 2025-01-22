// Copyright (c) 2025, jignasha and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Payment Report"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
			width: "100px",
			on_change: function() {
				// Set the 'to_date' automatically based on 'from_date'
				var from_date = frappe.query_report.get_filter_value("from_date");
				if (from_date) {
					var end_of_month = getEndOfMonth(from_date);
					frappe.query_report.set_filter_value("to_date", end_of_month);
				}
			}
		},
		{
			fieldname: "to_date",
			label: __("To"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
			reqd: 1,
			width: "100px",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			width: "100px",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "100px",
			reqd: 1,
		},
		{
			fieldname: "docstatus",
			label: __("Document Status"),
			fieldtype: "Select",
			options: ["Draft", "Submitted", "Cancelled"],
			default: "Submitted",
			width: "100px",
		},
	]
};

// Get the first day of the current month
function getCurrentMonthStartDate() {
	var today = new Date();
	var firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
	var year = firstDay.getFullYear();
	var month = (firstDay.getMonth() + 1).toString().padStart(2, '0');
	var date = firstDay.getDate().toString().padStart(2, '0');
	return `${year}-${month}-${date}`;
}

// Get the last day of the current month
function getCurrentMonthEndDate() {
	var today = new Date();
	var lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
	var year = lastDay.getFullYear();
	var month = (lastDay.getMonth() + 1).toString().padStart(2, '0');
	var date = lastDay.getDate().toString().padStart(2, '0');
	return `${year}-${month}-${date}`;
}

// Get the last day of the month for a given date
function getEndOfMonth(date) {
	var selectedDate = new Date(date);
	var lastDay = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);
	var year = lastDay.getFullYear();
	var month = (lastDay.getMonth() + 1).toString().padStart(2, '0');
	var day = lastDay.getDate().toString().padStart(2, '0');
	return `${year}-${month}-${day}`;
}
