# Copyright (c) 2024, jignasha and contributors
# For license information, please see license.txt

# import frappe

import frappe
import erpnext
from datetime import datetime

salary_slip = frappe.qb.DocType("Salary Slip")
custom_employer_contribution_table = frappe.qb.DocType("Custom Employer Contribution Table")
salary_component = frappe.qb.DocType("Salary Component")

def execute(filters=None):
    if not filters:
        filters = {}

    salary_slips = get_salary_slips(filters)
    if not salary_slips:
        return [], []

    # Gather all salary components across all Salary Slips (removed from data processing)
    all_salary_components = get_unique_salary_components(salary_slips)

    # Static columns for PF Employer, ESIC Employer, Gratuity, etc.
    static_columns = [
        {"label": "PF Employer", "fieldname": "pf_employer", "fieldtype": "Currency", "width": 120, "precision": 2},
        {"label": "ESIC Employer", "fieldname": "esic_employer", "fieldtype": "Currency", "width": 120, "precision": 2},
        {"label": "LWF Employer", "fieldname": "lwf_employer", "fieldtype": "Currency", "width": 120, "precision": 2},
        {"label": "Gratuity", "fieldname": "gratuity", "fieldtype": "Currency", "width": 120, "precision": 2},
        {"label": "Retirals PM", "fieldname": "retirals_pm", "fieldtype": "Currency", "width": 120, "precision": 2}
    ]

    # Combine the static columns
    columns = get_columns(all_salary_components) + static_columns

    data = []
    for ss in salary_slips:
        salary_slip_doc = frappe.get_doc("Salary Slip", ss.name)

        row = {
            "salary_slip_id": ss.name,
            "employee": ss.employee,
            "employee_name": ss.employee_name,
            "department": ss.department,
            "designation": ss.designation,
            "company": ss.company,
            "start_date": format_date(ss.start_date),
            "end_date": format_date(ss.end_date),
            "leave_without_pay": ss.leave_without_pay,
            "payment_days": ss.payment_days,
            "working_days": ss.total_working_days,
            "gross_salary": ss.gross_pay,
        }

        # Add the employer contribution columns
        row["pf_employer"] = get_employer_contribution_amount(salary_slip_doc, "PF Employer")
        row["esic_employer"] = get_employer_contribution_amount(salary_slip_doc, "ESIC Employer")
        row["lwf_employer"] = get_employer_contribution_amount(salary_slip_doc, "LWF Employer")
        row["gratuity"] = get_employer_contribution_amount(salary_slip_doc, "Gratuity")
        row["retirals_pm"] = get_employer_contribution_amount(salary_slip_doc, "Retirals PM")

        data.append(row)

    return columns, data

def format_date(date_value):
    """ Helper function to format dates in dd-mm-yyyy format """
    if date_value:
        return datetime.strptime(str(date_value), "%Y-%m-%d").strftime("%d-%m-%Y")
    return ""

def get_columns(all_salary_components):
    columns = [
        {
            "label": "Salary Slip ID",
            "fieldname": "salary_slip_id",
            "fieldtype": "Link",
            "options": "Salary Slip",
            "width": 150,
        },
        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120,
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": "Department",
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 120,
        },
        {
            "label": "Designation",
            "fieldname": "designation",
            "fieldtype": "Link",
            "options": "Designation",
            "width": 120,
        },
        {
            "label": "Company",
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 120,
        },
        {
            "label": "Start Date",
            "fieldname": "start_date",
            "fieldtype": "Data",
            "width": 80,
        },
        {
            "label": "End Date",
            "fieldname": "end_date",
            "fieldtype": "Data",
            "width": 80,
        },
        {
            "label": "LOP Days",
            "fieldname": "leave_without_pay",
            "fieldtype": "Float",
            "width": 100,
            "precision": 1,
        },
        {
            "label": "Payment Days",
            "fieldname": "payment_days",
            "fieldtype": "Float",
            "width": 120,
            "precision": 1,
        },
        {
            "label": "Working Days",
            "fieldname": "working_days",
            "fieldtype": "Float",
            "width": 120,
            "precision": 1,
        },
        {
            "label": "Gross Salary",
            "fieldname": "gross_salary",
            "fieldtype": "Currency",
            "width": 120,
            "precision": 2,
        },
    ]
    
    # Removed dynamic salary component columns here
    return columns

def get_unique_salary_components(salary_slips):
    salary_components = set()
    for ss in salary_slips:
        salary_slip_doc = frappe.get_doc("Salary Slip", ss.name)
        # Extract salary components from custom_employer_contribution_table
        for emp in salary_slip_doc.get('custom_employer_contribution_table'):
            salary_components.add(emp.salary_component)
            
    return list(salary_components)

def get_salary_component_amount(salary_slip_doc, salary_component):
    for emp in salary_slip_doc.get('custom_employer_contribution_table'):
        if emp.salary_component == salary_component:
            return emp.amount
    return 0

def get_employer_contribution_amount(salary_slip_doc, contribution_type):
    for emp in salary_slip_doc.get('custom_employer_contribution_table'):
        salary_component_doc = frappe.get_doc("Salary Component", emp.salary_component)
        if salary_component_doc.custom_employer_contribution_type == contribution_type:
            return emp.amount
    return 0

def get_salary_slips(filters):
    doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

    query = frappe.qb.from_(salary_slip).select(salary_slip.star)

    if filters.get("docstatus"):
        query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

    if filters.get("from_date"):
        query = query.where(salary_slip.start_date >= filters.get("from_date"))

    if filters.get("to_date"):
        query = query.where(salary_slip.end_date <= filters.get("to_date"))

    if filters.get("company"):
        query = query.where(salary_slip.company == filters.get("company"))

    if filters.get("employee"):
        query = query.where(salary_slip.employee == filters.get("employee"))

    salary_slips = query.run(as_dict=1)

    return salary_slips or []
