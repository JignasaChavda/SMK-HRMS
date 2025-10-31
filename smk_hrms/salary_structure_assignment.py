import frappe
from smk_hrms.overrides.salary_slip_override import evaluate_formula_parts

def before_print(self, method=None, print_format=None):
    calculated_earnings = []
    calculated_contributions = []
    variables = {"base": self.base or 0}

    if not self.salary_structure:
        return

    ss = frappe.get_doc("Salary Structure", self.salary_structure)

    # --- STEP 1: First Pass – Get direct values (no formulas) ---
    for e in ss.earnings:
        if not e.formula and e.amount:
            variables[e.abbr] = e.amount

    # --- STEP 2: Second Pass – Evaluate formulas ---
    for e in ss.earnings:
        formula = e.formula or ""
        amount = e.amount or 0

        if formula:
            evaluated_value, error = evaluate_formula_parts(formula, variables, self)
            if error:
                frappe.logger().error(f"[Earnings] Error evaluating {e.salary_component}: {error}")
                amount = 0
            else:
                amount = evaluated_value or 0

        variables[e.abbr] = amount  # update dict with evaluated value

        calculated_earnings.append({
            "salary_component": e.salary_component,
            "abbr": e.abbr,
            "amount": amount
        })

    self.custom_calculated_earnings = calculated_earnings

    # --- Employer Contribution Table ---
    if hasattr(ss, "custom_employer_contribution_table"):
        for c in ss.custom_employer_contribution_table:
            formula = getattr(c, "formula", None) or ""
            amount = c.amount or 0

            if formula:
                evaluated_value, error = evaluate_formula_parts(formula, variables, self)
                if error:
                    frappe.logger().error(f"[Employer Contribution] Error evaluating {c.salary_component}: {error}")
                    amount = 0
                else:
                    amount = evaluated_value or 0

            variables[c.abbr] = amount  # update dict for future references

            calculated_contributions.append({
                "salary_component": c.salary_component,
                "abbr": c.abbr if hasattr(c, "abbr") else "",
                "amount": amount
            })

    self.custom_calculated_employer_contribution = calculated_contributions
