# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import re
import json
from frappe import _
from frappe.utils import now_datetime, cint

class SecurityManager:
    """
    Security manager for handling data protection and masking in Gemini integration.
    
    This class provides methods for masking sensitive data, checking permissions,
    and implementing role-based security features.
    """
    
    def __init__(self):
        """Initialize the security manager."""
        self.settings = frappe.get_single("Gemini Assistant Settings")
        self.sensitive_keywords = self._load_sensitive_keywords()
    
    def _load_sensitive_keywords(self):
        """
        Load sensitive keywords from the database.
        
        Returns:
            list: List of sensitive keyword configurations
        """
        try:
            keywords = []
            keyword_docs = frappe.get_all(
                "Gemini Sensitive Keyword",
                filters={"enabled": 1},
                fields=["keyword_pattern", "replacement_pattern", "is_global", "specific_doctypes", "specific_fields"]
            )
            
            for kw in keyword_docs:
                keywords.append({
                    "pattern": kw.keyword_pattern,
                    "replacement": kw.replacement_pattern,
                    "is_global": cint(kw.is_global),
                    "doctypes": kw.specific_doctypes,
                    "fields": [f.strip() for f in (kw.specific_fields or "").split(",") if f.strip()]
                })
            
            return keywords
        except Exception as e:
            frappe.log_error(f"Error loading sensitive keywords: {str(e)}")
            return []
    
    def mask_sensitive_data(self, text, doctype=None, field=None):
        """
        Mask sensitive data in text based on configured patterns.
        
        Args:
            text (str): Text to mask
            doctype (str, optional): Current doctype context
            field (str, optional): Current field context
            
        Returns:
            str: Text with sensitive data masked
        """
        if not text or not isinstance(text, str):
            return text
            
        masked_text = text
        
        # Apply configured sensitive keywords
        for keyword in self.sensitive_keywords:
            # Check if keyword applies to this context
            if not keyword["is_global"]:
                # Skip if doctype doesn't match
                if doctype and keyword["doctypes"] and doctype not in keyword["doctypes"]:
                    continue
                    
                # Skip if field doesn't match
                if field and keyword["fields"] and field not in keyword["fields"]:
                    continue
            
            try:
                # Apply the regex pattern
                masked_text = re.sub(
                    keyword["pattern"],
                    keyword["replacement"],
                    masked_text
                )
            except Exception as e:
                frappe.log_error(f"Error applying sensitive keyword pattern: {str(e)}")
        
        # Apply default masking for common patterns if enabled
        if self.settings.enable_role_based_security:
            # Mask email addresses
            masked_text = re.sub(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                '[EMAIL REDACTED]',
                masked_text
            )
            
            # Mask phone numbers
            masked_text = re.sub(
                r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
                '[PHONE REDACTED]',
                masked_text
            )
            
            # Mask credit card numbers
            masked_text = re.sub(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                '[CREDIT CARD REDACTED]',
                masked_text
            )
            
            # Mask SSN/SIN numbers
            masked_text = re.sub(
                r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
                '[SSN REDACTED]',
                masked_text
            )
        
        return masked_text
    
    def check_field_permission(self, doctype, field, perm_type="read"):
        """
        Check if the current user has permission for a specific field.
        
        Args:
            doctype (str): DocType to check
            field (str): Field to check
            perm_type (str, optional): Permission type. Defaults to "read".
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        try:
            # Check if user has permission for the doctype
            if not frappe.has_permission(doctype, perm_type):
                return False
            
            # Get user roles
            user_roles = frappe.get_roles(frappe.session.user)
            
            # Check if System Manager (has all permissions)
            if "System Manager" in user_roles:
                return True
            
            # Check field level permissions if available
            meta = frappe.get_meta(doctype)
            field_obj = meta.get_field(field)
            
            if not field_obj:
                return False
                
            # Check if field is hidden or read-only for non-read operations
            if perm_type != "read" and (field_obj.hidden or field_obj.read_only):
                return False
            
            # Check if field has explicit permissions
            if hasattr(field_obj, "permlevel") and field_obj.permlevel > 0:
                # Get permission level for the field
                permlevel = field_obj.permlevel
                
                # Check if user has permission at this level
                has_perm = False
                for role in user_roles:
                    role_perms = frappe.permissions.get_role_permissions(doctype, role)
                    if role_perms.get(f"permlevel_{permlevel}", {}).get(perm_type):
                        has_perm = True
                        break
                
                return has_perm
            
            # Default to True if no specific field permissions are defined
            return True
            
        except Exception as e:
            frappe.log_error(f"Error checking field permission: {str(e)}")
            return False
    
    def get_safe_document_data(self, doctype, docname, fields=None):
        """
        Get document data with sensitive information masked and permissions checked.
        
        Args:
            doctype (str): DocType to get
            docname (str): Document name
            fields (list, optional): Specific fields to get
            
        Returns:
            dict: Safe document data
        """
        try:
            # Check if user has read permission for the doctype
            if not frappe.has_permission(doctype, "read"):
                return {"error": "Permission denied", "success": False}
            
            # Get the document
            doc = frappe.get_doc(doctype, docname)
            
            # Get all fields or specific fields
            safe_data = {}
            meta = frappe.get_meta(doctype)
            
            field_list = fields if fields else [f.fieldname for f in meta.fields]
            
            for fieldname in field_list:
                # Check field permission
                if not self.check_field_permission(doctype, fieldname):
                    continue
                
                # Get field value
                if hasattr(doc, fieldname):
                    value = doc.get(fieldname)
                    if value is not None:
                        # Convert to string and mask sensitive data
                        str_value = str(value)
                        masked_value = self.mask_sensitive_data(str_value, doctype, fieldname)
                        safe_data[fieldname] = masked_value
            
            return {"data": safe_data, "success": True}
            
        except Exception as e:
            frappe.log_error(f"Error getting safe document data: {str(e)}")
            return {"error": str(e), "success": False}
    
    def log_security_event(self, event_type, details, status="Success"):
        """
        Log a security event to the audit log.
        
        Args:
            event_type (str): Type of security event
            details (dict): Event details
            status (str, optional): Event status. Defaults to "Success".
        """
        try:
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Function Call",
                "details": json.dumps({
                    "function": "security_manager",
                    "event_type": event_type,
                    "details": details
                }),
                "status": status,
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging security event: {str(e)}")


# Function to mask sensitive data (for direct import)
def mask_sensitive_data(text, doctype=None, field=None):
    """
    Mask sensitive data in text based on configured patterns.
    
    Args:
        text (str): Text to mask
        doctype (str, optional): Current doctype context
        field (str, optional): Current field context
        
    Returns:
        str: Text with sensitive data masked
    """
    security_manager = SecurityManager()
    return security_manager.mask_sensitive_data(text, doctype, field)
