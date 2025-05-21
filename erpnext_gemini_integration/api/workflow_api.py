# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import now_datetime, cint
from ..utils.workflow_engine import WorkflowEngine

def setup_document_hooks():
    """
    Set up document event hooks for workflow automation.
    
    This function registers the necessary hooks for document events
    to trigger workflow automation.
    """
    # Register document hooks in hooks.py
    # This is a placeholder function as actual hooks are defined in hooks.py
    pass

@frappe.whitelist()
def process_document_event(doctype, docname, event, user=None):
    """
    Process a document event and trigger appropriate workflows.
    
    Args:
        doctype (str): DocType of the document
        docname (str): Name of the document
        event (str): Event type (e.g., "on_update", "after_insert")
        user (str, optional): User who triggered the event
        
    Returns:
        dict: Result of workflow processing
    """
    try:
        # Initialize workflow engine
        workflow_engine = WorkflowEngine()
        
        # Process the event
        result = workflow_engine.process_document_event(doctype, docname, event, user)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error processing document event: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def execute_custom_action(action_name, params=None):
    """
    Execute a custom action defined in the system.
    
    Args:
        action_name (str): Name of the custom action
        params (dict or str, optional): Parameters for the action
        
    Returns:
        dict: Result of action execution
    """
    try:
        # Parse params if provided as string
        if params and isinstance(params, str):
            try:
                params = json.loads(params)
            except Exception:
                return {
                    "success": False,
                    "error": "Invalid parameters format"
                }
        
        # Initialize workflow engine
        workflow_engine = WorkflowEngine()
        
        # Execute the action
        result = workflow_engine.execute_custom_action(action_name, params)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error executing custom action: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_ai_recommendation(doctype, docname, context=None):
    """
    Get AI recommendations for a document.
    
    Args:
        doctype (str): DocType of the document
        docname (str): Name of the document
        context (dict or str, optional): Additional context
        
    Returns:
        dict: AI recommendations
    """
    try:
        # Parse context if provided as string
        if context and isinstance(context, str):
            try:
                context = json.loads(context)
            except Exception:
                context = {}
        
        # Initialize workflow engine
        workflow_engine = WorkflowEngine()
        
        # Get recommendations
        result = workflow_engine.get_ai_recommendation(doctype, docname, context)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error getting AI recommendation: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_available_actions(doctype=None, user=None):
    """
    Get available custom actions for a user.
    
    Args:
        doctype (str, optional): Filter actions by doctype
        user (str, optional): User to check permissions for
        
    Returns:
        list: List of available actions
    """
    try:
        # This would typically query a custom DocType for action definitions
        # For now, we'll return a hardcoded example
        actions = [
            {
                "name": "send_email",
                "description": "Send an email to specified recipients",
                "parameters": ["recipients", "subject", "message"]
            },
            {
                "name": "create_task",
                "description": "Create a new task",
                "parameters": ["subject", "description", "assigned_to"]
            }
        ]
        
        # Filter by doctype if provided
        if doctype:
            # In a real implementation, this would filter actions by doctype
            pass
        
        # Filter by user permissions
        if user:
            # In a real implementation, this would check user permissions
            pass
        
        return actions
        
    except Exception as e:
        frappe.log_error(f"Error getting available actions: {str(e)}")
        return []

@frappe.whitelist()
def register_document_event_handler(doctype, event, handler_module, handler_function):
    """
    Register a custom document event handler.
    
    Args:
        doctype (str): DocType to register handler for
        event (str): Event type (e.g., "on_update", "after_insert")
        handler_module (str): Python module containing the handler
        handler_function (str): Function name to call
        
    Returns:
        dict: Registration result
    """
    try:
        # Check if user has permission
        if not frappe.has_permission("Gemini Assistant Settings", "write"):
            return {"success": False, "error": "Permission denied"}
        
        # This would typically store the handler in a custom DocType
        # For now, we'll just log it
        frappe.log_error(f"Registered handler: {doctype}.{event} -> {handler_module}.{handler_function}")
        
        return {
            "success": True,
            "message": f"Handler registered for {doctype}.{event}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error registering document event handler: {str(e)}")
        return {"success": False, "error": str(e)}
