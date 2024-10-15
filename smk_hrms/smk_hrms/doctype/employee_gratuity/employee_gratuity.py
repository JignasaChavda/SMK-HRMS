# Copyright (c) 2024, jignasha and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeGratuity(Document):
	pass
	
@frappe.whitelist()
def get_last_basic(last_salary_slip):
		sal_doc = frappe.get_doc('Salary Slip', last_salary_slip)
		ear_child = sal_doc.get("earnings")
		for child in ear_child:
			if child.salary_component == 'Basic':
				basic_amount = child.amount
				return basic_amount