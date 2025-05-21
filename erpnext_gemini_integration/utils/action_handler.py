# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import now_datetime, cint

class ActionHandler:
    """
    Custom action handler for workflow automation.
    
    This class provides methods for defining, registering, and executing
    custom actions that can be used in workflow automation.
    """
    
    def __init__(self):
        """Initialize the action handler."""
        self.settings = frappe.get_single("Gemini Assistant Settings")
        self.registered_actions = self._load_registered_actions()
    
    def register_action(self, action_name, description, handler_module, handler_function, allowed_roles=None, parameters=None):
        """
        Register a new custom action.
        
        Args:
            action_name (str): Name of the action
            description (str): Description of the action
            handler_module (str): Python module containing the handler
            handler_function (str): Function name to call
            allowed_roles (list, optional): Roles allowed to execute this action
            parameters (list, optional): Required parameters for the action
            
        Returns:
            dict: Registration result
        """
        try:
            # Check if action already exists
            if action_name in self.registered_actions:
                return {"success": False, "error": f"Action '{action_name}' already exists"}
            
            # Create action definition
            action = {
                "name": action_name,
                "description": description,
                "handler_module": handler_module,
                "handler_function": handler_function,
                "allowed_roles": allowed_roles or ["System Manager"],
                "parameters": parameters or []
            }
            
            # Save action definition
            # In a real implementation, this would save to a custom DocType
            self.registered_actions[action_name] = action
            
            # Log the registration
            self._log_action_registration(action)
            
            return {
                "success": True,
                "message": f"Action '{action_name}' registered successfully"
            }
            
        except Exception as e:
            frappe.log_error(f"Error registering action: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def execute_action(self, action_name, params=None, user=None):
        """
        Execute a registered custom action.
        
        Args:
            action_name (str): Name of the action to execute
            params (dict, optional): Parameters for the action
            user (str, optional): User executing the action
            
        Returns:
            dict: Result of action execution
        """
        try:
            # Check if action exists
            if action_name not in self.registered_actions:
                return {"success": False, "error": f"Action '{action_name}' not found"}
            
            # Get action definition
            action = self.registered_actions[action_name]
            
            # Check permissions
            if not self._check_action_permissions(action, user or frappe.session.user):
                return {"success": False, "error": "Permission denied"}
            
            # Validate parameters
            if not self._validate_parameters(action, params):
                return {"success": False, "error": "Missing or invalid parameters"}
            
            # Import handler module
            handler_module = frappe.get_module(action["handler_module"])
            
            # Get handler function
            handler_function = getattr(handler_module, action["handler_function"])
            
            # Execute handler
            result = handler_function(params)
            
            # Log the execution
            self._log_action_execution(action_name, params, result)
            
            return result
            
        except Exception as e:
            frappe.log_error(f"Error executing action: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_available_actions(self, doctype=None, user=None):
        """
        Get available custom actions for a user.
        
        Args:
            doctype (str, optional): Filter actions by doctype
            user (str, optional): User to check permissions for
            
        Returns:
            list: List of available actions
        """
        try:
            available_actions = []
            
            # Get user if not provided
            user = user or frappe.session.user
            
            # Check each registered action
            for action_name, action in self.registered_actions.items():
                # Check permissions
                if self._check_action_permissions(action, user):
                    # Add to available actions
                    available_actions.append({
                        "name": action["name"],
                        "description": action["description"],
                        "parameters": action["parameters"]
                    })
            
            return available_actions
            
        except Exception as e:
            frappe.log_error(f"Error getting available actions: {str(e)}")
            return []
    
    def _load_registered_actions(self):
        """
        Load registered actions from the database.
        
        Returns:
            dict: Dictionary of registered actions
        """
        # In a real implementation, this would load from a custom DocType
        # For now, we'll return a hardcoded example
        return {
            "send_email": {
                "name": "send_email",
                "description": "Send an email to specified recipients",
                "handler_module": "erpnext_gemini_integration.utils.action_handlers",
                "handler_function": "handle_send_email",
                "allowed_roles": ["System Manager", "Administrator"],
                "parameters": ["recipients", "subject", "message"]
            },
            "create_task": {
                "name": "create_task",
                "description": "Create a new task",
                "handler_module": "erpnext_gemini_integration.utils.action_handlers",
                "handler_function": "handle_create_task",
                "allowed_roles": ["System Manager", "Administrator"],
                "parameters": ["subject", "description", "assigned_to"]
            }
        }
    
    def _check_action_permissions(self, action, user):
        """
        Check if a user has permission to execute an action.
        
        Args:
            action (dict): Action definition
            user (str): User to check
            
        Returns:
            bool: True if user has permission
        """
        # Get user roles
        user_roles = frappe.get_roles(user)
        
        # Check if user has any of the allowed roles
        allowed_roles = action.get("allowed_roles", [])
        
        for role in user_roles:
            if role in allowed_roles or role == "Administrator":
                return True
        
        return False
    
    def _validate_parameters(self, action, params):
        """
        Validate parameters for an action.
        
        Args:
            action (dict): Action definition
            params (dict): Parameters to validate
            
        Returns:
            bool: True if parameters are valid
        """
        # Check if all required parameters are provided
        required_params = action.get("parameters", [])
        
        if not params:
            return not required_params
        
        for param in required_params:
            if param not in params:
                return False
        
        return True
    
    def _log_action_registration(self, action):
        """
        Log action registration to the audit log.
        
        Args:
            action (dict): Action definition
        """
        try:
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Action Registration",
                "details": json.dumps({
                    "action_name": action["name"],
                    "description": action["description"],
                    "handler": f"{action['handler_module']}.{action['handler_function']}",
                    "timestamp": str(now_datetime())
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging action registration: {str(e)}")
    
    def _log_action_execution(self, action_name, params, result):
        """
        Log action execution to the audit log.
        
        Args:
            action_name (str): Name of the action
            params (dict): Action parameters
            result (dict): Result of action execution
        """
        try:
            # Create a safe copy of params without sensitive data
            safe_params = {}
            for key, value in (params or {}).items():
                if key not in ["password", "api_key", "token"]:
                    safe_params[key] = value
            
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Action Execution",
                "details": json.dumps({
                    "action": action_name,
                    "params": safe_params,
                    "success": result.get("success", False),
                    "timestamp": str(now_datetime())
                }),
                "status": "Success" if result.get("success") else "Error",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging action execution: {str(e)}")
