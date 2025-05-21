import frappe
from frappe.model.document import Document

class GeminiFeedback(Document):
    def validate(self):
        # Add validation logic here if needed
        pass
        
    def after_insert(self):
        # Update related message or conversation with feedback
        if self.message:
            frappe.db.set_value('Gemini Message', self.message, 'feedback_rating', self.rating)
            frappe.db.set_value('Gemini Message', self.message, 'feedback_comments', self.comments) 