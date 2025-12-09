// Copyright (c) 2025, jignasha and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Performance Evaluation Report"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From"),
			fieldtype: "Date",
			reqd: 1,
			width: "100px",
		
		},
		{
			fieldname: "to_date",
			label: __("To"),
			fieldtype: "Date",
			reqd: 1,
			width: "100px",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			width: "100px",
		}
	]
};
