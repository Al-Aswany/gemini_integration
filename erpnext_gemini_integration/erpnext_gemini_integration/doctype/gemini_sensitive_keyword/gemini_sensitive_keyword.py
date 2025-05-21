import frappe
from frappe.model.document import Document

class GeminiSensitiveKeyword(Document):
    def validate(self):
        # Ensure keyword is not empty
        if not self.keyword or not self.keyword.strip():
            frappe.throw('Keyword cannot be empty')
            
        # Convert to lowercase for consistency
        self.keyword = self.keyword.strip().lower() 