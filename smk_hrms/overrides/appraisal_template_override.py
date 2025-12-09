import frappe
from hrms.hr.doctype.appraisal_template.appraisal_template import AppraisalTemplate

class CustomAppraisalTemplate(AppraisalTemplate):

    def validate(self):
        self.validate_total_weightage("goals", "KRAs")

        # skip default HRMS mixin validation
        # pass
