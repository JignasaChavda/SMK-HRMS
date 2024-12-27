import frappe
from frappe import _
from hrms.hr.doctype.leave_application.leave_application import validate_active_employee
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip as TransactionBase, sanitize_expression
import re
from frappe.utils import formatdate, getdate

class SalarySlip(TransactionBase):
    def validate(self):
        self.check_salary_withholding()
        self.status = self.get_status()
        validate_active_employee(self.employee)
        self.validate_dates()
        self.check_existing()
        
        if not self.salary_slip_based_on_timesheet:
            self.get_date_details()
        
        
        if not (len(self.get("earnings")) or len(self.get("deductions"))):
			
            self.get_emp_and_working_day_details()
        else:
            self.get_working_days_details(lwp=self.leave_without_pay)

        self.set_salary_structure_assignment()
        if self.is_new():
            self.calculate_net_pay()
        self.compute_year_to_date()
        self.compute_month_to_date()
        self.compute_component_wise_year_to_date()

        self.add_leave_balances()
        if not self.is_new():
            self.calculate_employer_contribution()

        max_working_hours = frappe.db.get_single_value(
            "Payroll Settings", "max_working_hours_against_timesheet"
        )
        if max_working_hours:
            if self.salary_slip_based_on_timesheet and (self.total_working_hours > int(max_working_hours)):
                frappe.msgprint(
                    _("Total working hours should not be greater than max working hours {0}").format(
                        max_working_hours
                    ),
                    alert=True,
                )

    

    def calculate_employer_contribution(self):
        
        emp = self.employee
        salary_structure = self.salary_structure
        start_date = self.start_date  # Example: 2024-07-24
        formatted_date = formatdate(start_date, "dd-mm-yyyy")  # Format to dd-mm-yyyy
        start_month = getdate(start_date).month  # Extract the month from the start_date
        # frappe.msgprint(_("Formatted Start Date: {0}, Month: {1}").format(formatted_date, start_month))
        if not self.custom_employer_contribution_table:
            if not salary_structure:
                frappe.throw(_("Salary Structure is not set in the Salary Slip"))

            # Fetch Salary Structure and Assignment
            salary_structure_doc = frappe.get_doc("Salary Structure", salary_structure)
            salary_structure_assignment = frappe.get_all(
                "Salary Structure Assignment",
                filters={"employee": emp, "salary_structure": salary_structure},
                fields=["base"]
            )
            
            if not salary_structure_assignment:
                frappe.throw(_("No Salary Structure Assignment found for this employee and salary structure."))
            
            base = salary_structure_assignment[0].base
            abbr = "B"  # The abbreviation you want to look for

            # Fetch salary component for abbreviation 'B'
            component_name, component_value = find_salary_component_from_abbr(self, abbr)

            # If component is None or 0, skip processing this component
            if component_name is None or component_value == 0:            
                component_value = 0 

            # frappe.msgprint(_("Found Salary Component: {0}, Amount: {1}").format(component_name, component_value))

            # Prepare variables for formula evaluation
            variables = {"B": component_value, "base": base, "start_month": start_month}
        
            self.custom_employer_contribution_table = []
        
            # Iterate through custom employer contribution table and evaluate formulas
            for row in salary_structure_doc.custom_employer_contribution_table:
                # Replace "getdate(start_date).month" dynamically with `start_month`
                formula = row.formula.replace("getdate(start_date).month", str(start_month))
                evaluated_formula, error = evaluate_formula_parts(formula, variables)
                if error:
                    # frappe.msgprint(error)
                    continue
                
                self.append("custom_employer_contribution_table", {
                    "salary_component": row.salary_component,
                    "formula": formula,
                    "amount": evaluated_formula
                })
            

            # Notify the user
            # frappe.msgprint(_("Employee: {0}<br>Salary Structure: {1}<br>Base: {2}<br>Salary Components and Formulas have been added.").format(
            #     emp, salary_structure, base), title=_("Details")
            # )


def evaluate_formula_parts(formula, variables):
    """Evaluate formulas with variables, including if-else expressions and direct amounts."""
    try:
        # Check if the formula is a direct number (e.g., "1800" or "2000")
        if formula.isdigit():
            return float(formula), None
        
        # If the formula contains a ternary condition (if-else expression), process it
        match = re.match(r'\((.*?)\)\s*if\s*(.*?)\s*else\s*(.*)', formula)
        if match:
            true_expr, condition_expr, false_expr = match.groups()
            
            # Replace start_date and handle the month condition
            if 'start_date' in condition_expr:
                # Evaluate the condition based on the month of start_date
                condition_expr = condition_expr.replace("getdate(start_date).month", str(frappe.utils.getdate(self.start_date).month))
                
            condition_result = eval_salary_formula(condition_expr, variables)
            return (eval_salary_formula(true_expr, variables) if condition_result else eval_salary_formula(false_expr, variables)), None
       
        # If no ternary condition, simply evaluate the formula
        return eval_salary_formula(formula, variables), None
        
    except Exception as e:
        return None, f"Error evaluating formula '{formula}': {str(e)}"

def eval_salary_formula(formula, variables):
    """Safely evaluate formulas by replacing variables."""
    try:
        for var, value in variables.items():
            formula = formula.replace(var, str(value))
        return eval(formula)
    except Exception as e:
        return None, f"Error in formula evaluation: {str(e)}"



def find_salary_component_from_abbr(self, abbr):
    """Find the salary component value and name by abbreviation."""
    salary_slip_doc = frappe.get_doc("Salary Slip", self.name)

    # Search in earnings and deductions
    for table in [salary_slip_doc.earnings, salary_slip_doc.deductions]:
        for item in table:
            if item.salary_component and item.abbr == abbr:
                return item.salary_component, item.amount

    return None, 0


