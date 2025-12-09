import frappe

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
            "width": 120
        },
        {
            "label": "KRA",
            "fieldname": "kra",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": "Standard Weightage of KRA (%)",
            "fieldname": "standard_weightage_of_kra",
            "fieldtype": "Float",
            "width": 180,
            "precision": 2
        },
        # {
        #     "label": "KPI",
        #     "fieldname": "kpi",
        #     "fieldtype": "Data",
        #     "width": 200
        # },
        # {
        #     "label": "Standard Weightage of KPI (%)",
        #     "fieldname": "standard_weightage_of_kpi",
        #     "fieldtype": "Float",
        #     "width": 180,
        #     "precision": 2
        # },
        # {
        #     "label": "Total Progress (%)",
        #     "fieldname": "progress",
        #     "fieldtype": "Float",
        #     "width": 120,
        #     "precision": 2
        # },
        # {
        #     "label": "Achieved Weightage",
        #     "fieldname": "achieved_weightage",
        #     "fieldtype": "Float",
        #     "width": 150,
        #     "precision": 2
        # },
        {
            "label": "Total Received KRA Weightage",
            "fieldname": "total_received_kra_weightage",
            "fieldtype": "Float",
            "width": 200,
            "precision": 2
        }
    ]

# def get_data(filters):
#     data = []
    
#     # Build conditions for WPT query
#     conditions = {}
    
#     if filters.get("from_date"):
#         conditions["week_from_date"] = [">=", filters.get("from_date")]
    
#     if filters.get("to_date"):
#         conditions["week_to_date"] = ["<=", filters.get("to_date")]
    
#     if filters.get("employee"):
#         conditions["employee"] = filters.get("employee")
    
#     if filters.get("department"):
#         conditions["department"] = filters.get("department")

#     # Get employees from Weekly Progress Tracker within date range
#     wpt_employees = frappe.get_all(
#         "Weekly Progress Tracker",
#         filters=conditions,
#         fields=["employee"],
#         distinct=True
#     )
    
#     for employee_row in wpt_employees:
#         employee = employee_row.employee
        
#         # Get employee details
#         employee_details = frappe.db.get_value(
#             "Employee", 
#             employee, 
#             ["employee_name", "designation", "department"], 
#             as_dict=True
#         )
        
#         if not employee_details:
#             continue
            
#         designation = employee_details.designation
        
#         if not designation:
#             continue

#         # Get Appraisal Template from Designation
#         appraisal_template = frappe.db.get_value(
#             "Designation", 
#             designation, 
#             "appraisal_template"
#         )
        
#         if not appraisal_template:
#             continue

#         # ---- STEP 1: Get Standard KRA Weightage from Appraisal Template Goal ----
#         template_goals = frappe.get_all(
#             "Appraisal Template Goal",
#             filters={"parent": appraisal_template},
#             fields=["key_result_area", "per_weightage"]
#         )
        
#         if not template_goals:
#             continue
        
#         # Create dictionary of standard KRA weightages
#         standard_kra_weightages = {}
#         for goal in template_goals:
#             kra = goal.key_result_area
#             try:
#                 standard_weight = float(goal.per_weightage) if goal.per_weightage else 0.0
#             except (ValueError, TypeError):
#                 standard_weight = 0.0
#             standard_kra_weightages[kra] = standard_weight

#         # ---- STEP 2: Get KPI to KRA mapping and weightages from Employee Feedback Rating ----
#         rating_criteria = frappe.get_all(
#             "Employee Feedback Rating",
#             filters={"parent": appraisal_template},
#             fields=["criteria", "custom_kra", "per_weightage"]
#         )
        
#         # Create mapping: (kpi, kra) -> weightage
#         kpi_kra_mapping = {}
#         for criteria in rating_criteria:
#             kpi_name = criteria.criteria
#             kra_name = criteria.custom_kra
#             try:
#                 kpi_weightage = float(criteria.per_weightage) if criteria.per_weightage else 0.0
#             except (ValueError, TypeError):
#                 kpi_weightage = 0.0
            
#             # Create a composite key for matching
#             key = (kpi_name, kra_name)
#             kpi_kra_mapping[key] = kpi_weightage

#         # ---- STEP 3: Get all WPT records for this employee ----
#         wpt_records = frappe.get_all(
#             "Weekly Progress Tracker",
#             filters={
#                 "employee": employee,
#                 "week_from_date": [">=", filters.get("from_date")] if filters.get("from_date") else None,
#                 "week_to_date": ["<=", filters.get("to_date")] if filters.get("to_date") else None
#             },
#             fields=["name"]
#         )

#         # Dictionary to store SUM of progress for each (kpi, kra) combination
#         kpi_progress_sum = {}  # {(kpi, kra): total_progress}
        
#         # Process each WPT record to get SUM of progress
#         for wpt in wpt_records:
#             # Get KRA-KPI details from child table
#             kra_kpi_details = frappe.get_all(
#                 "KRA-KPI Details",
#                 filters={"parent": wpt.name},
#                 fields=["kpi", "kra", "progress"]
#             )
            
#             for detail in kra_kpi_details:
#                 kpi = detail.kpi
#                 kra = detail.kra
#                 key = (kpi, kra)
                
#                 # Convert progress to float
#                 try:
#                     progress = float(detail.progress) if detail.progress else 0.0
#                 except (ValueError, TypeError):
#                     progress = 0.0
                
#                 # Initialize if first time
#                 if key not in kpi_progress_sum:
#                     kpi_progress_sum[key] = 0.0
                
#                 # SUM the progress (not average)
#                 kpi_progress_sum[key] += progress

#         # ---- STEP 4: Create hierarchical report structure ----
#         for kra, standard_kra_weight in standard_kra_weightages.items():
#             # Initialize KRA totals
#             total_kra_achieved = 0.0
            
#             # Add KRA row (indent 0)
#             data.append({
#                 "employee": employee,
#                 "kra": kra,
#                 "standard_weightage_of_kra": standard_kra_weight,
#                 "kpi": "",
#                 "standard_weightage_of_kpi": "",
#                 "progress": "",
#                 "achieved_weightage": "",
#                 "total_received_kra_weightage": "",
#                 "indent": 0
#             })
            
#             # Find all KPIs for this KRA from rating criteria
#             kpis_for_kra = []
#             for (kpi_name, kra_name), kpi_weightage in kpi_kra_mapping.items():
#                 if kra_name == kra:
#                     kpis_for_kra.append({
#                         "kpi": kpi_name,
#                         "weightage": kpi_weightage
#                     })
            
#             # Process each KPI
#             for kpi_info in kpis_for_kra:
#                 kpi = kpi_info["kpi"]
#                 kpi_weightage = kpi_info["weightage"]
#                 key = (kpi, kra)
                
#                 # Get SUM progress if available
#                 total_progress = kpi_progress_sum.get(key, 0.0)
                
#                 # Calculate achieved weightage: (total_progress / 100) × kpi_weightage
#                 achieved_weightage = (total_progress *kpi_weightage)
                
#                 # Add to KRA total
#                 # total_kra_achieved += achieved_weightage*standard_kra_weight/100.0
#                 standard_kra_weight = standard_kra_weight/100.0
#                 achieved_weightage = achieved_weightage/100.0
#                 total_kra_achieved += standard_kra_weight/52.0 * achieved_weightage *100

                
#                 # Add KPI row (indent 1)
#                 data.append({
#                     "employee": "",
#                     "kra": "",
#                     "standard_weightage_of_kra": "",
#                     "kpi": kpi,
#                     "standard_weightage_of_kpi": kpi_weightage,
#                     "progress": total_progress,
#                     "achieved_weightage": achieved_weightage,
#                     "total_received_kra_weightage": "",
#                     "indent": 1
#                 })
            
#             # Update the KRA row with total received weightage
#             for i in range(len(data) - len(kpis_for_kra) - 1, len(data)):
#                 if data[i].get("kra") == kra and data[i].get("indent") == 0:
#                     data[i]["total_received_kra_weightage"] = total_kra_achieved
#                     break

#     return data


def get_data(filters):
    data = []
    
    # Build conditions for WPT query
    conditions = {}
    
    if filters.get("from_date"):
        conditions["week_from_date"] = [">=", filters.get("from_date")]
    
    if filters.get("to_date"):
        conditions["week_to_date"] = ["<=", filters.get("to_date")]
    
    if filters.get("employee"):
        conditions["employee"] = filters.get("employee")
    
    if filters.get("department"):
        conditions["department"] = filters.get("department")

    # Get employees from Weekly Progress Tracker within date range
    wpt_employees = frappe.get_all(
        "Weekly Progress Tracker",
        filters=conditions,
        fields=["employee"],
        distinct=True
    )
    
    for employee_row in wpt_employees:
        employee = employee_row.employee
        
        # Get employee details
        employee_details = frappe.db.get_value(
            "Employee", 
            employee, 
            ["employee_name", "designation", "department"], 
            as_dict=True
        )
        
        if not employee_details:
            continue
            
        designation = employee_details.designation
        
        if not designation:
            continue

        # Get Appraisal Template from Designation
        appraisal_template = frappe.db.get_value(
            "Designation", 
            designation, 
            "appraisal_template"
        )
        
        if not appraisal_template:
            continue

        # ---- STEP 1: Get Standard KRA Weightage from Appraisal Template Goal ----
        template_goals = frappe.get_all(
            "Appraisal Template Goal",
            filters={"parent": appraisal_template},
            fields=["key_result_area", "per_weightage"]
        )
        
        if not template_goals:
            continue
        
        # Create dictionary of standard KRA weightages
        standard_kra_weightages = {}
        for goal in template_goals:
            kra = goal.key_result_area
            try:
                standard_weight = float(goal.per_weightage) if goal.per_weightage else 0.0
            except (ValueError, TypeError):
                standard_weight = 0.0
            standard_kra_weightages[kra] = standard_weight

        # ---- STEP 2: Get KPI to KRA mapping and weightages from Employee Feedback Rating ----
        rating_criteria = frappe.get_all(
            "Employee Feedback Rating",
            filters={"parent": appraisal_template},
            fields=["criteria", "custom_kra", "per_weightage"]
        )
        
        # Create mapping: (kpi, kra) -> weightage
        kpi_kra_mapping = {}
        for criteria in rating_criteria:
            kpi_name = criteria.criteria
            kra_name = criteria.custom_kra
            try:
                kpi_weightage = float(criteria.per_weightage) if criteria.per_weightage else 0.0
            except (ValueError, TypeError):
                kpi_weightage = 0.0
            
            # Create a composite key for matching
            key = (kpi_name, kra_name)
            kpi_kra_mapping[key] = kpi_weightage

        # ---- STEP 3: Get all WPT records for this employee ----
        wpt_records = frappe.get_all(
            "Weekly Progress Tracker",
            filters={
                "employee": employee,
                "week_from_date": [">=", filters.get("from_date")] if filters.get("from_date") else None,
                "week_to_date": ["<=", filters.get("to_date")] if filters.get("to_date") else None
            },
            fields=["name"]
        )

        # Dictionary to store SUM of progress for each (kpi, kra) combination
        kpi_progress_sum = {}  # {(kpi, kra): total_progress}
        
        # Process each WPT record to get SUM of progress
        for wpt in wpt_records:
            # Get KRA-KPI details from child table
            kra_kpi_details = frappe.get_all(
                "KRA-KPI Details",
                filters={"parent": wpt.name},
                fields=["kpi", "kra", "progress"]
            )
            
            for detail in kra_kpi_details:
                kpi = detail.kpi
                kra = detail.kra
                key = (kpi, kra)
                
                # Convert progress to float
                try:
                    progress = float(detail.progress) if detail.progress else 0.0
                except (ValueError, TypeError):
                    progress = 0.0
                
                # Initialize if first time
                if key not in kpi_progress_sum:
                    kpi_progress_sum[key] = 0.0
                
                # SUM the progress (not average)
                kpi_progress_sum[key] += progress

        # ---- STEP 4: Create hierarchical report structure ----
        for kra, standard_kra_weight in standard_kra_weightages.items():
            # Initialize KRA totals
            total_kra_achieved = 0.0
            
            # Add KRA row (indent 0)
            data.append({
                "employee": employee,
                "kra": kra,
                "standard_weightage_of_kra": round(standard_kra_weight, 2),
                "kpi": "",
                "standard_weightage_of_kpi": "",
                "progress": "",
                "achieved_weightage": "",
                "total_received_kra_weightage": "",
                "indent": 0
            })
            
            # Find all KPIs for this KRA from rating criteria
            kpis_for_kra = []
            for (kpi_name, kra_name), kpi_weightage in kpi_kra_mapping.items():
                if kra_name == kra:
                    kpis_for_kra.append({
                        "kpi": kpi_name,
                        "weightage": kpi_weightage
                    })
            
            # Process each KPI
            for kpi_info in kpis_for_kra:
                kpi = kpi_info["kpi"]
                kpi_weightage = kpi_info["weightage"]
                key = (kpi, kra)
                
                # Get SUM progress if available
                total_progress = kpi_progress_sum.get(key, 0.0)
                
                # Calculate achieved weightage: (total_progress / 100) × kpi_weightage
                achieved_weightage = (total_progress / 100.0) * kpi_weightage
                
                # Add to KRA total
                standard_kra_weight_percent = standard_kra_weight / 100.0
                achieved_weightage_percent = achieved_weightage / 100.0
                
                total_for_kpi = (standard_kra_weight_percent / 52.0) * achieved_weightage_percent * 100.0
                total_for_kpi = round(total_for_kpi, 2)
                
                total_kra_achieved += total_for_kpi
                
                # Add KPI row (indent 1)
                data.append({
                    "employee": "",
                    "kra": "",
                    "standard_weightage_of_kra": "",
                    "kpi": kpi,
                    "standard_weightage_of_kpi": round(kpi_weightage, 2),
                    "progress": round(total_progress, 2),
                    "achieved_weightage": round(achieved_weightage, 2),
                    "total_received_kra_weightage": "",
                    "indent": 1
                })
            
            # Update the KRA row with total received weightage
            for i in range(len(data) - len(kpis_for_kra) - 1, len(data)):
                if data[i].get("kra") == kra and data[i].get("indent") == 0:
                    data[i]["total_received_kra_weightage"] = round(total_kra_achieved, 2)
                    break

    return data