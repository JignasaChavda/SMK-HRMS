import frappe
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

    # Gather all salary components across all Salary Slips and group them by custom_salary_component_type for earnings and deductions
    salary_components_by_type = get_salary_components_grouped_by_type(salary_slips)

    # Static columns for basic information about Salary Slip (no PF, ESIC, etc.)
    columns = get_columns(salary_components_by_type)

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

        # Add dynamic columns for grouped salary components (both earnings and deductions)
        for component_type, components in salary_components_by_type.items():
            total_amount = 0
            for component in components:
                total_amount += get_salary_component_amount(salary_slip_doc, component)
            row[component_type] = total_amount

        # Add the Net Salary at the end
        row["net_salary"] = ss.net_pay

        data.append(row)

    return columns, data

def format_date(date_value):
    """ Helper function to format dates in dd-mm-yyyy format """
    if date_value:
        return datetime.strptime(str(date_value), "%Y-%m-%d").strftime("%d-%m-%Y")
    return ""

def get_columns(salary_components_by_type):
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

    # Add dynamic columns for each custom_salary_component_type (for both earnings and deductions)
    for component_type in salary_components_by_type:
        columns.append({
            "label": component_type,
            "fieldname": component_type,
            "fieldtype": "Currency",
            "width": 120,
            "precision": 2,
        })

    # Add the Net Salary column at the end
    columns.append({
        "label": "Net Salary",
        "fieldname": "net_salary",
        "fieldtype": "Currency",
        "width": 120,
        "precision": 2,
    })

    return columns

def get_salary_components_grouped_by_type(salary_slips):
    salary_components_by_type = {}

    for ss in salary_slips:
        salary_slip_doc = frappe.get_doc("Salary Slip", ss.name)
        
        # Extract salary components from earnings
        for emp in salary_slip_doc.get('earnings'):
            salary_component_doc = frappe.get_doc("Salary Component", emp.salary_component)
            component_type = salary_component_doc.custom_salary_component_type

            if component_type not in salary_components_by_type:
                salary_components_by_type[component_type] = []

            if emp.salary_component not in salary_components_by_type[component_type]:
                salary_components_by_type[component_type].append(emp.salary_component)

        # Extract salary components from deductions (similar to earnings)
        for emp in salary_slip_doc.get('deductions'):
            salary_component_doc = frappe.get_doc("Salary Component", emp.salary_component)
            component_type = salary_component_doc.custom_salary_component_type

            if component_type not in salary_components_by_type:
                salary_components_by_type[component_type] = []

            if emp.salary_component not in salary_components_by_type[component_type]:
                salary_components_by_type[component_type].append(emp.salary_component)

    return salary_components_by_type

def get_salary_component_amount(salary_slip_doc, salary_component):
    # Check in earnings
    for emp in salary_slip_doc.get('earnings'):
        if emp.salary_component == salary_component:
            return emp.amount

    # Check in deductions
    for emp in salary_slip_doc.get('deductions'):
        if emp.salary_component == salary_component:
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
