import frappe
from frappe.model.document import Document

class GeminiConversation(Document):
    def validate(self):
        # Add validation logic here if needed
        pass
        
    def on_update(self):
        # Add update logic here if needed
        pass
        
    def get_messages(self):
        # Method to get all messages in this conversation
        return frappe.get_all('Gemini Message',
            filters={'conversation': self.name},
            fields=['name', 'message', 'response', 'timestamp'],
            order_by='timestamp'
        ) 