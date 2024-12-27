 # Earned Leave Allocation       
import frappe
from frappe.utils.data import getdate, now, today
from frappe.utils import getdate, today, add_days, date_diff

@frappe.whitelist(allow_guest=True)
def custom_earned_leave_allocation():
    
    current_date = getdate(today())

    leave_allocation = frappe.db.get_all('Leave Allocation', 
        filters={
            'docstatus': 1,
            'from_date': ['<=', current_date],
            'to_date': ['>=', current_date],
        },
        fields=['*']
    )

    def update_leave_allocation(la_name, new_allocation_value):
        frappe.db.set_value(
            'Leave Allocation',
            la_name.name,
            {'new_leaves_allocated': new_allocation_value, 'total_leaves_allocated': new_allocation_value}
        )
        frappe.db.commit()
    # return current_date
    for la in leave_allocation:
        la_name = frappe.get_doc('Leave Allocation', la.name)

        leave_type = la.leave_type
        effective_from_date = la.from_date
        effective_to_date = la.to_date
        tot_allocated_leaves = la.total_leaves_allocated

        leave_type_doc = frappe.get_doc('Leave Type', leave_type)
        max_allocation = leave_type_doc.max_leaves_allowed
        allocation_day = leave_type_doc.allocate_on_day
        is_sick_leave = leave_type_doc.custom_is_sick_leave
        earned_leave_frequency = leave_type_doc.earned_leave_frequency
        monthly_allocation = leave_type_doc.custom_monthly_allocation_for_sick_leave
        last_month_allocation = leave_type_doc.custom_monthly_allocation_for_last_month        
        # return current_date
        if is_sick_leave==1 and earned_leave_frequency=="Monthly":            
            end_date = frappe.utils.getdate(effective_to_date)
            last_day_of_current_month = frappe.utils.get_last_day(current_date)
            is_last_month = (current_date.year == end_date.year and current_date.month == end_date.month)

            if is_last_month==True:
                if allocation_day == 'First Day':
                    first_day_of_last_month = frappe.utils.get_first_day(last_day_of_current_month.replace(month=current_date.month))
                    if current_date == first_day_of_last_month:
                        monthly_allocation_for_last_month = leave_type_doc.custom_monthly_allocation_for_last_month
                        new_allocation_value = la_name.new_leaves_allocated + monthly_allocation_for_last_month
                        maximum_leave_allocation = leave_type_doc.max_leaves_allowed
                        if new_allocation_value <= maximum_leave_allocation:
                            update_leave_allocation(la_name, new_allocation_value)
                else:
                    last_day_of_last_month = frappe.utils.get_last_day(last_day_of_current_month.replace(month=current_date.month))                    
                    if current_date == last_day_of_last_month:
                        monthly_allocation_for_last_month = leave_type_doc.custom_monthly_allocation_for_last_month
                        new_allocation_value = la_name.new_leaves_allocated + monthly_allocation_for_last_month
                        maximum_leave_allocation = leave_type_doc.max_leaves_allowed
                        if new_allocation_value <= maximum_leave_allocation:
                            update_leave_allocation(la_name, new_allocation_value)
                        
            else:
                if allocation_day == 'First Day':
                    first_day_of_current_month = frappe.utils.get_first_day(last_day_of_current_month.replace(month=current_date.month))                    
                    if current_date == first_day_of_current_month:
                        monthly_allocation_for_current_month = leave_type_doc.custom_monthly_allocation_for_sick_leave
                        new_allocation_value = la_name.new_leaves_allocated + monthly_allocation_for_current_month
                        maximum_leave_allocation = leave_type_doc.max_leaves_allowed
                        if new_allocation_value <= maximum_leave_allocation:
                            update_leave_allocation(la_name, new_allocation_value)
                else:
                    last_day_of_current_month = frappe.utils.get_last_day(last_day_of_current_month.replace(month=current_date.month))                    
                    if current_date == last_day_of_current_month:
                        monthly_allocation_for_current_month = leave_type_doc.custom_monthly_allocation_for_sick_leave
                        new_allocation_value = la_name.new_leaves_allocated + monthly_allocation_for_current_month
                        maximum_leave_allocation = leave_type_doc.max_leaves_allowed
                        if new_allocation_value <= maximum_leave_allocation:
                           update_leave_allocation(la_name, new_allocation_value)
    return           