import frappe
from frappe.model.document import Document
from frappe.utils import now

class GeminiMessage(Document):
    def validate(self):
        if not self.timestamp:
            self.timestamp = now()
            
    def before_save(self):
        # Check for sensitive keywords if enabled
        self.check_sensitive_keywords()
        
    def check_sensitive_keywords(self):
        # Get sensitive keywords from settings
        keywords = frappe.get_all('Gemini Sensitive Keyword',
            fields=['keyword'],
            filters={'parent': 'Gemini Assistant Settings'}
        )
        
        # Check message content against keywords
        for kw in keywords:
            if kw.keyword.lower() in self.message.lower():
                frappe.throw(
                    f"Message contains sensitive keyword: {kw.keyword}. Please revise your message."
                ) 