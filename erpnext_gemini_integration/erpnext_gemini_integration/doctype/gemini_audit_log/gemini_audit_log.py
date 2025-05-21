import frappe
from frappe.model.document import Document

class GeminiAuditLog(Document):
    def validate(self):
        # Add validation logic here if needed
        pass
        
    def after_insert(self):
        # Add any post-insert logic here
        pass 