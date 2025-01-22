import frappe
from datetime import datetime

salary_structure = frappe.qb.DocType("Salary Structure")

def execute(filters=None):
    if not filters:
        filters = {}

    salary_structures = get_salary_structure(filters)
    if not salary_structures:
        return [], []

    # Initialize sets to track encountered component types
    earnings_types = []
    deduction_types = []
    employer_contribution_types = []

    # Collect components in the order they appear
    collect_ordered_component_types(salary_structures, earnings_types, deduction_types, employer_contribution_types)

    # Define columns dynamically, ensuring order of categories based on first encountered components
    columns = get_columns(earnings_types, deduction_types, employer_contribution_types)

    data = []
    for ss in salary_structures:
        salary_structure_doc = frappe.get_doc("Salary Structure", ss.name)

        row = {"salary_structure": ss.name, "company": ss.company}

        # Process earnings to populate dynamic columns
        process_components(salary_structure_doc.get("earnings", []), row)

        # Process deductions to populate dynamic columns
        process_components(salary_structure_doc.get("deductions", []), row)

        # Process custom_employer_contribution_table to populate dynamic columns
        process_components(salary_structure_doc.get("custom_employer_contribution_table", []), row)

        data.append(row)

    return columns, data


def process_components(components, row):
    """Process components (earnings, deductions, employer contributions) to populate dynamic columns."""
    for component in components:
        salary_component_doc = frappe.get_doc("Salary Component", component.salary_component)
        component_type = salary_component_doc.custom_salary_component_type

        if component_type:
            if component_type not in row:
                row[component_type] = ''  # Initialize column if not present

            # Handle NoneType in formula
            formula_value = component.formula if component.formula is not None else ""

            # Add the formula value to the column
            row[component_type] += formula_value


def get_columns(earnings_types, deduction_types, employer_contribution_types):
    """Create dynamic columns for each custom_salary_component_type, ordered by first encountered component."""
    columns = [
        {
            "label": "Salary Structure",
            "fieldname": "salary_structure",
            "fieldtype": "Link",
            "options": "Salary Structure",
            "width": 150,
        },
        {
            "label": "Company",
            "fieldname": "company",
            "fieldtype": "Data",
            "width": 200,
        },
    ]

    # Add columns for Earnings in the order they were first encountered
    for component_type in earnings_types:
        columns.append({
            "label": component_type,
            "fieldname": component_type,
            "fieldtype": "Data",
            "width": 150,
        })

    # Add columns for Deductions in the order they were first encountered
    for component_type in deduction_types:
        columns.append({
            "label": component_type,
            "fieldname": component_type,
            "fieldtype": "Data",
            "width": 150,
        })

    # Add columns for Employer Contributions in the order they were first encountered
    for component_type in employer_contribution_types:
        columns.append({
            "label": component_type,
            "fieldname": component_type,
            "fieldtype": "Data",
            "width": 150,
        })

    return columns


def collect_ordered_component_types(salary_structures, earnings_types, deduction_types, employer_contribution_types):
    """Collect components in the order they appear in the first salary structure."""
    for ss in salary_structures:
        salary_structure_doc = frappe.get_doc("Salary Structure", ss.name)

        # Process earnings to capture order of components
        collect_ordered_component_types_from_list(salary_structure_doc.get("earnings", []), earnings_types)

        # Process deductions to capture order of components
        collect_ordered_component_types_from_list(salary_structure_doc.get("deductions", []), deduction_types)

        # Process employer contributions to capture order of components
        collect_ordered_component_types_from_list(salary_structure_doc.get("custom_employer_contribution_table", []), employer_contribution_types)


def collect_ordered_component_types_from_list(components, component_types):
    """Helper function to collect component types in the order they appear."""
    for component in components:
        salary_component_doc = frappe.get_doc("Salary Component", component.salary_component)
        component_type = salary_component_doc.custom_salary_component_type

        if component_type and component_type not in component_types:
            component_types.append(component_type)


def get_salary_structure(filters):
    """Fetch salary structures based on filters."""
    doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

    query = frappe.qb.from_(salary_structure).select(salary_structure.star)

    if filters.get("docstatus"):
        query = query.where(salary_structure.docstatus == doc_status[filters.get("docstatus")])

    if filters.get("company"):
        query = query.where(salary_structure.company == filters.get("company"))

    salary_structures = query.run(as_dict=1)

    return salary_structures or []
