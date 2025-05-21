# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import now_datetime, cint
from ..gemini.exceptions import GeminiContextError

class ContextManager:
    """
    Context manager for handling conversation context and history in Gemini integration.
    
    This class provides methods for managing conversation context, including
    conversation history, document context, and user session context.
    """
    
    def __init__(self):
        """Initialize the context manager."""
        self.settings = frappe.get_single("Gemini Assistant Settings")
        self.max_history_messages = 10  # Default value
        self.context_cache = {}
    
    def get_conversation_context(self, conversation_id, include_history=True):
        """
        Get the full context for a conversation.
        
        Args:
            conversation_id (str): Conversation ID
            include_history (bool, optional): Whether to include conversation history
            
        Returns:
            dict: Context dictionary with conversation details
        """
        try:
            # Check if context is enabled
            if not self.settings.enable_context_awareness:
                return {"context_enabled": False}
            
            # Get conversation details
            conversation = frappe.get_doc("Gemini Conversation", conversation_id)
            
            # Build context dictionary
            context = {
                "conversation_id": conversation_id,
                "user": conversation.user,
                "start_time": str(conversation.start_time),
                "context_enabled": True
            }
            
            # Add doctype context if available
            if conversation.context_doctype:
                context["doctype"] = conversation.context_doctype
                
                if conversation.context_docname:
                    context["docname"] = conversation.context_docname
                    
                    # Add document fields if both doctype and docname are provided
                    try:
                        from ..utils.security import SecurityManager
                        security_manager = SecurityManager()
                        doc_data = security_manager.get_safe_document_data(
                            conversation.context_doctype, 
                            conversation.context_docname
                        )
                        
                        if doc_data.get("success"):
                            context["document_data"] = doc_data.get("data", {})
                    except Exception as e:
                        frappe.log_error(f"Error getting document data for context: {str(e)}")
            
            # Add conversation history if requested
            if include_history:
                context["conversation_history"] = self.get_conversation_history(conversation_id)
            
            # Log context retrieval
            self._log_context_retrieval(conversation_id, context)
            
            return context
            
        except Exception as e:
            frappe.log_error(f"Error getting conversation context: {str(e)}")
            raise GeminiContextError(f"Error getting conversation context: {str(e)}")
    
    def get_conversation_history(self, conversation_id, max_messages=None):
        """
        Get the conversation history formatted for context.
        
        Args:
            conversation_id (str): Conversation ID
            max_messages (int, optional): Maximum number of messages to include
            
        Returns:
            str: Formatted conversation history
        """
        try:
            # Use provided max_messages or default
            limit = max_messages or self.max_history_messages
            
            # Get messages
            messages = frappe.get_all(
                "Gemini Message",
                filters={"conversation": conversation_id},
                fields=["role", "content"],
                order_by="timestamp asc",
                limit=limit
            )
            
            if not messages:
                return ""
            
            # Format history
            history = ""
            for msg in messages:
                history += f"{msg.role}: {msg.content}\n\n"
            
            return history
            
        except Exception as e:
            frappe.log_error(f"Error getting conversation history: {str(e)}")
            return ""
    
    def get_active_doctype_context(self):
        """
        Get context information for the active doctype.
        
        Returns:
            dict: Context dictionary with active doctype details
        """
        try:
            # Check if context is enabled
            if not self.settings.enable_context_awareness:
                return {"context_enabled": False}
            
            # Get current route
            route = frappe.get_route()
            
            # Check if on a form page
            if len(route) >= 3 and route[0] == "Form":
                doctype = route[1]
                docname = route[2]
                
                # Get document metadata
                meta = frappe.get_meta(doctype)
                
                # Build context
                context = {
                    "doctype": doctype,
                    "docname": docname,
                    "module": meta.module,
                    "context_enabled": True
                }
                
                # Get document fields
                try:
                    from ..utils.security import SecurityManager
                    security_manager = SecurityManager()
                    doc_data = security_manager.get_safe_document_data(doctype, docname)
                    
                    if doc_data.get("success"):
                        context["document_data"] = doc_data.get("data", {})
                except Exception as e:
                    frappe.log_error(f"Error getting document data for active context: {str(e)}")
                
                return context
            
            # Check if on a list page
            elif len(route) >= 2 and route[0] == "List":
                doctype = route[1]
                
                # Get doctype metadata
                meta = frappe.get_meta(doctype)
                
                # Build context
                context = {
                    "doctype": doctype,
                    "module": meta.module,
                    "view": "List",
                    "context_enabled": True
                }
                
                return context
            
            # Default context
            return {
                "route": route,
                "context_enabled": True
            }
            
        except Exception as e:
            frappe.log_error(f"Error getting active doctype context: {str(e)}")
            return {"context_enabled": False, "error": str(e)}
    
    def update_conversation_context(self, conversation_id, context_data):
        """
        Update the context for a conversation.
        
        Args:
            conversation_id (str): Conversation ID
            context_data (dict): New context data
            
        Returns:
            bool: Success status
        """
        try:
            # Get conversation
            conversation = frappe.get_doc("Gemini Conversation", conversation_id)
            
            # Update doctype and docname if provided
            if "doctype" in context_data:
                conversation.context_doctype = context_data["doctype"]
                
            if "docname" in context_data:
                conversation.context_docname = context_data["docname"]
            
            # Save changes
            conversation.save(ignore_permissions=True)
            frappe.db.commit()
            
            # Update cache
            self._update_context_cache(conversation_id, context_data)
            
            # Log context update
            self._log_context_update(conversation_id, context_data)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Error updating conversation context: {str(e)}")
            return False
    
    def detect_context_change(self, conversation_id, current_context):
        """
        Detect if the context has changed significantly.
        
        Args:
            conversation_id (str): Conversation ID
            current_context (dict): Current context data
            
        Returns:
            bool: True if context has changed significantly
        """
        try:
            # Get cached context
            cached_context = self._get_context_cache(conversation_id)
            
            if not cached_context:
                # No cached context, consider it changed
                self._update_context_cache(conversation_id, current_context)
                return True
            
            # Check for significant changes
            significant_change = False
            
            # Check doctype change
            if cached_context.get("doctype") != current_context.get("doctype"):
                significant_change = True
            
            # Check docname change
            elif cached_context.get("docname") != current_context.get("docname"):
                significant_change = True
            
            # Update cache if changed
            if significant_change:
                self._update_context_cache(conversation_id, current_context)
            
            return significant_change
            
        except Exception as e:
            frappe.log_error(f"Error detecting context change: {str(e)}")
            return False
    
    def _get_context_cache(self, conversation_id):
        """
        Get cached context for a conversation.
        
        Args:
            conversation_id (str): Conversation ID
            
        Returns:
            dict: Cached context or None
        """
        return self.context_cache.get(conversation_id)
    
    def _update_context_cache(self, conversation_id, context_data):
        """
        Update cached context for a conversation.
        
        Args:
            conversation_id (str): Conversation ID
            context_data (dict): Context data to cache
        """
        self.context_cache[conversation_id] = context_data
    
    def _log_context_retrieval(self, conversation_id, context):
        """
        Log context retrieval to the audit log.
        
        Args:
            conversation_id (str): Conversation ID
            context (dict): Retrieved context
        """
        try:
            # Create a safe copy of context without sensitive data
            safe_context = {
                "conversation_id": conversation_id,
                "context_enabled": context.get("context_enabled", False),
                "has_doctype": "doctype" in context,
                "has_docname": "docname" in context,
                "has_history": "conversation_history" in context,
                "timestamp": str(now_datetime())
            }
            
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Function Call",
                "details": json.dumps({
                    "function": "context_manager",
                    "action": "context_retrieval",
                    "details": safe_context
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging context retrieval: {str(e)}")
    
    def _log_context_update(self, conversation_id, context_data):
        """
        Log context update to the audit log.
        
        Args:
            conversation_id (str): Conversation ID
            context_data (dict): Updated context data
        """
        try:
            # Create a safe copy of context without sensitive data
            safe_context = {
                "conversation_id": conversation_id,
                "updated_fields": list(context_data.keys()),
                "timestamp": str(now_datetime())
            }
            
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Function Call",
                "details": json.dumps({
                    "function": "context_manager",
                    "action": "context_update",
                    "details": safe_context
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging context update: {str(e)}")
