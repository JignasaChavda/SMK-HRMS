import frappe
from frappe.utils import formatdate

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "label": "Employee",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 200,
        },
        {
            "label": "KRA",
            "fieldname": "kra",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Standard Weightage of KRA (%)",
            "fieldname": "standard_weightage_of_kra",
            "fieldtype": "Float",
            "width": 200,
            "precision": 2,
        },
        {
            "label": "Total Received KRA Weightage",
            "fieldname": "total_received_kra_weightage",
            "fieldtype": "Float",
            "width": 250,
            "precision": 2,
        },
        {
            "label": "Remarks",
            "fieldname": "remarks",
            "fieldtype": "Long Text",
            "width": 365,
            "align": "left",
        },
    ]


def get_data(filters):
    data = []

    conditions = {}

    if filters.get("from_date"):
        conditions["week_from_date"] = [">=", filters.get("from_date")]

    if filters.get("to_date"):
        conditions["week_to_date"] = ["<=", filters.get("to_date")]

    if filters.get("employee"):
        conditions["employee"] = filters.get("employee")

    if filters.get("department"):
        conditions["department"] = filters.get("department")

    # employees from WPT
    wpt_employees = frappe.get_all(
        "Weekly Progress Tracker",
        filters=conditions,
        fields=["employee", "employee_name"],
        distinct=True,
    )

    for employee_row in wpt_employees:
        employee = employee_row.employee
        employee_name = employee_row.employee_name

        employee_details = frappe.db.get_value(
            "Employee",
            employee,
            ["designation", "department"],
            as_dict=True,
        )
        if not employee_details:
            continue

        designation = employee_details.designation
        if not designation:
            continue

        appraisal_template = frappe.db.get_value(
            "Designation",
            designation,
            "appraisal_template",
        )
        if not appraisal_template:
            continue

        # ---- STEP 1: Standard KRA weightage ----
        template_goals = frappe.get_all(
            "Appraisal Template Goal",
            filters={"parent": appraisal_template},
            fields=["key_result_area", "per_weightage"],
        )
        if not template_goals:
            continue

        standard_kra_weightages = {}
        for goal in template_goals:
            kra = goal.key_result_area
            try:
                standard_weight = float(goal.per_weightage) if goal.per_weightage else 0.0
            except (ValueError, TypeError):
                standard_weight = 0.0
            standard_kra_weightages[kra] = standard_weight

        # ---- STEP 2: KPI–KRA mapping ----
        rating_criteria = frappe.get_all(
            "Employee Feedback Rating",
            filters={"parent": appraisal_template},
            fields=["criteria", "custom_kra", "per_weightage"],
        )

        kpi_kra_mapping = {}
        for criteria in rating_criteria:
            kpi_name = criteria.criteria
            kra_name = criteria.custom_kra
            try:
                kpi_weightage = float(criteria.per_weightage) if criteria.per_weightage else 0.0
            except (ValueError, TypeError):
                kpi_weightage = 0.0

            key = (kpi_name, kra_name)
            kpi_kra_mapping[key] = kpi_weightage

        # ---- STEP 3: WPT records ----
        wpt_filters = {"employee": employee}
        if filters.get("from_date"):
            wpt_filters["week_from_date"] = [">=", filters.get("from_date")]
        if filters.get("to_date"):
            wpt_filters["week_to_date"] = ["<=", filters.get("to_date")]

        wpt_records = frappe.get_all(
            "Weekly Progress Tracker",
            filters=wpt_filters,
            fields=["name", "week_from_date", "week_to_date"],
            order_by="week_from_date asc",
        )

        kpi_progress_sum = {}
        # Store remarks grouped by date range
        remarks_by_date = []

        for wpt in wpt_records:
            wpt_doc = frappe.get_doc("Weekly Progress Tracker", wpt.name)
            
            # Format date range
            from_date_str = formatdate(wpt.week_from_date, "dd/MM/yy") if wpt.week_from_date else ""
            to_date_str = formatdate(wpt.week_to_date, "dd/MM/yy") if wpt.week_to_date else ""
            date_range = f"{from_date_str} - {to_date_str}"
            
            # Collect remarks for this date range
            date_remarks = {
                "date_range": date_range,
                "hr": "",
                "self": "",
                "manager": ""
            }
            
            if wpt_doc.remarks_hr and wpt_doc.remarks_hr.strip():
                date_remarks["hr"] = wpt_doc.remarks_hr.strip()
            
            if wpt_doc.remarks_self and wpt_doc.remarks_self.strip():
                date_remarks["self"] = wpt_doc.remarks_self.strip()
            
            if wpt_doc.remarks_manager and wpt_doc.remarks_manager.strip():
                date_remarks["manager"] = wpt_doc.remarks_manager.strip()
            
            # Only add if there are any remarks
            if date_remarks["hr"] or date_remarks["self"] or date_remarks["manager"]:
                remarks_by_date.append(date_remarks)

            # Collect KPI progress
            kra_kpi_details = frappe.get_all(
                "KRA-KPI Details",
                filters={"parent": wpt.name},
                fields=["kpi", "kra", "progress"],
            )

            for detail in kra_kpi_details:
                kpi = detail.kpi
                kra = detail.kra
                key = (kpi, kra)

                try:
                    progress = float(detail.progress) if detail.progress else 0.0
                except (ValueError, TypeError):
                    progress = 0.0

                if key not in kpi_progress_sum:
                    kpi_progress_sum[key] = 0.0
                kpi_progress_sum[key] += progress

        # ---- STEP 4: build remark text exactly like image ----
        remarks_text = ""
        
        for i, date_remarks in enumerate(remarks_by_date):
            if i > 0:
                remarks_text += "\n\n"
            
            # Date line - exactly like in image
            remarks_text += f"DATE: {date_remarks['date_range']}"
            
            # HR Remarks
            if date_remarks["hr"]:
                remarks_text += f"\nHR REMARKS\n"
                remarks_text += f"{date_remarks['hr']}"
            
            # Self Remarks
            if date_remarks["self"]:
                remarks_text += f"\nSELF REMARKS\n"
                remarks_text += f"{date_remarks['self']}"
            
            # Manager Remarks
            if date_remarks["manager"]:
                remarks_text += f"\nMANAGER REMARKS\n"
                remarks_text += f"{date_remarks['manager']}"

        # ---- STEP 5: KRA totals ----
        kra_totals = {}

        for kra, standard_kra_weight in standard_kra_weightages.items():
            total_kra_achieved = 0.0

            kpis_for_kra = []
            for (kpi_name, kra_name), kpi_weightage in kpi_kra_mapping.items():
                if kra_name == kra:
                    kpis_for_kra.append(
                        {"kpi": kpi_name, "weightage": kpi_weightage}
                    )

            for kpi_info in kpis_for_kra:
                kpi = kpi_info["kpi"]
                kpi_weightage = kpi_info["weightage"]
                key = (kpi, kra)

                total_progress = kpi_progress_sum.get(key, 0.0)

                achieved_weightage = (total_progress / 100.0) * kpi_weightage
                standard_kra_weight_percent = standard_kra_weight / 100.0
                achieved_weightage_percent = achieved_weightage / 100.0

                total_for_kpi = (
                    (standard_kra_weight_percent / 52.0)
                    * achieved_weightage_percent
                    * 100.0
                )
                total_for_kpi = round(total_for_kpi, 2)

                total_kra_achieved += total_for_kpi

            kra_totals[kra] = {
                "standard_weight": standard_kra_weight,
                "total_received": round(total_kra_achieved, 2),
            }

        # ---- STEP 6: rows ----
        kra_list = list(kra_totals.items())
        employee_added = False

        for kra, totals in kra_list:
            if not employee_added:
                # Row 1: employee code + first KRA + all remarks
                data.append(
                    {
                        "employee": employee,
                        "kra": kra,
                        "standard_weightage_of_kra": round(
                            totals["standard_weight"], 2
                        ),
                        "total_received_kra_weightage": totals["total_received"],
                        "remarks": remarks_text,  # All remarks in first row
                        "indent": 0,
                    }
                )

                # Row 2: employee name only (no remarks)
                data.append(
                    {
                        "employee": employee_name,
                        "kra": "",
                        "standard_weightage_of_kra": "",
                        "total_received_kra_weightage": "",
                        "remarks": "",  # No remarks here
                        "indent": 0,
                    }
                )

                employee_added = True
            else:
                # other KRAs for same employee, after remarks
                data.append(
                    {
                        "employee": "",
                        "kra": kra,
                        "standard_weightage_of_kra": round(
                            totals["standard_weight"], 2
                        ),
                        "total_received_kra_weightage": totals["total_received"],
                        "remarks": "",
                        "indent": 0,
                    }
                )

    return data