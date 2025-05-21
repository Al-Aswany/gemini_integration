# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import now_datetime, cint
from ..gemini.client import GeminiClient
from ..gemini.prompt_builder import PromptBuilder
from ..gemini.response_parser import ResponseParser
from ..gemini.exceptions import GeminiWorkflowError

class RoleBasedAutomation:
    """
    Role-based automation rules for workflow automation.
    
    This class provides methods for defining, managing, and executing
    role-based automation rules in the Gemini integration.
    """
    
    def __init__(self):
        """Initialize the role-based automation manager."""
        self.settings = frappe.get_single("Gemini Assistant Settings")
        self.client = GeminiClient()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
    
    def get_applicable_rules(self, doctype, event, user=None):
        """
        Get automation rules applicable to a doctype, event, and user.
        
        Args:
            doctype (str): DocType of the document
            event (str): Event type (e.g., "on_update", "after_insert")
            user (str, optional): User who triggered the event
            
        Returns:
            list: List of applicable automation rules
        """
        try:
            # Check if role-based automation is enabled
            if not self.settings.enable_workflow_automation:
                return []
            
            # Get user roles
            user = user or frappe.session.user
            user_roles = frappe.get_roles(user)
            
            # Get all automation rules
            rules = self._get_automation_rules()
            
            # Filter rules by doctype, event, and user roles
            applicable_rules = []
            
            for rule in rules:
                # Check if rule applies to this doctype
                if rule.get("doctype") != doctype and rule.get("doctype") != "*":
                    continue
                
                # Check if rule applies to this event
                if rule.get("event") != event and rule.get("event") != "*":
                    continue
                
                # Check if user has required role
                role_match = False
                for role in user_roles:
                    if role in rule.get("allowed_roles", []) or role == "Administrator":
                        role_match = True
                        break
                
                if not role_match:
                    continue
                
                # Rule is applicable
                applicable_rules.append(rule)
            
            return applicable_rules
            
        except Exception as e:
            frappe.log_error(f"Error getting applicable rules: {str(e)}")
            return []
    
    def execute_rule(self, rule, doc, event, user=None):
        """
        Execute an automation rule on a document.
        
        Args:
            rule (dict): Automation rule definition
            doc (object): Document object
            event (str): Event type
            user (str, optional): User who triggered the event
            
        Returns:
            dict: Result of rule execution
        """
        try:
            # Get rule actions
            actions = rule.get("actions", [])
            
            # Execute each action
            results = []
            
            for action in actions:
                action_type = action.get("type")
                
                if action_type == "execute_action":
                    # Execute custom action
                    from ..utils.action_handler import ActionHandler
                    
                    action_handler = ActionHandler()
                    action_name = action.get("action_name")
                    params = action.get("params", {})
                    
                    # Replace placeholders in params
                    params = self._replace_placeholders(params, doc)
                    
                    # Execute action
                    result = action_handler.execute_action(action_name, params, user)
                    results.append({
                        "type": "execute_action",
                        "action": action_name,
                        "result": result
                    })
                
                elif action_type == "ai_decision":
                    # Make AI-driven decision
                    decision_result = self._make_ai_decision(action, doc, event, user)
                    results.append({
                        "type": "ai_decision",
                        "result": decision_result
                    })
                
                elif action_type == "condition":
                    # Evaluate condition
                    condition_result = self._evaluate_condition(action, doc)
                    results.append({
                        "type": "condition",
                        "result": condition_result
                    })
                    
                    # Skip remaining actions if condition is false
                    if not condition_result.get("condition_met", False):
                        break
            
            # Log the rule execution
            self._log_rule_execution(rule, results)
            
            return {
                "rule": rule.get("name"),
                "success": True,
                "actions_executed": len(results),
                "results": results
            }
            
        except Exception as e:
            frappe.log_error(f"Error executing rule: {str(e)}")
            return {
                "rule": rule.get("name"),
                "success": False,
                "error": str(e)
            }
    
    def create_rule(self, name, doctype, event, allowed_roles, actions, description=None, enabled=True):
        """
        Create a new automation rule.
        
        Args:
            name (str): Rule name
            doctype (str): DocType to apply rule to
            event (str): Event type to trigger rule
            allowed_roles (list): Roles allowed to trigger rule
            actions (list): Actions to execute
            description (str, optional): Rule description
            enabled (bool, optional): Whether rule is enabled
            
        Returns:
            dict: Result of rule creation
        """
        try:
            # Check if user has permission
            if not frappe.has_permission("Gemini Assistant Settings", "write"):
                return {"success": False, "error": "Permission denied"}
            
            # Create rule definition
            rule = {
                "name": name,
                "doctype": doctype,
                "event": event,
                "allowed_roles": allowed_roles,
                "actions": actions,
                "description": description or f"Rule for {doctype} on {event}",
                "enabled": enabled,
                "created_by": frappe.session.user,
                "created_at": str(now_datetime())
            }
            
            # Save rule
            # In a real implementation, this would save to a custom DocType
            # For now, we'll just log it
            frappe.log_error(f"Created rule: {json.dumps(rule)}")
            
            # Log the rule creation
            self._log_rule_creation(rule)
            
            return {
                "success": True,
                "message": f"Rule '{name}' created successfully"
            }
            
        except Exception as e:
            frappe.log_error(f"Error creating rule: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_automation_rules(self):
        """
        Get all automation rules.
        
        Returns:
            list: List of automation rules
        """
        # In a real implementation, this would query a custom DocType
        # For now, we'll return a hardcoded example
        return [
            {
                "name": "notify_admin_on_po_submit",
                "doctype": "Purchase Order",
                "event": "on_submit",
                "allowed_roles": ["Purchase Manager", "System Manager"],
                "description": "Notify admin when Purchase Order is submitted",
                "enabled": True,
                "actions": [
                    {
                        "type": "execute_action",
                        "action_name": "send_email",
                        "params": {
                            "recipients": ["administrator@example.com"],
                            "subject": "Purchase Order Submitted: {name}",
                            "message": "Purchase Order {name} has been submitted by {modified_by}."
                        }
                    }
                ]
            },
            {
                "name": "create_task_on_so_submit",
                "doctype": "Sales Order",
                "event": "on_submit",
                "allowed_roles": ["Sales Manager", "System Manager"],
                "description": "Create task when Sales Order is submitted",
                "enabled": True,
                "actions": [
                    {
                        "type": "execute_action",
                        "action_name": "create_task",
                        "params": {
                            "subject": "Process Sales Order: {name}",
                            "description": "Sales Order {name} has been submitted and needs processing.",
                            "assigned_to": "administrator@example.com"
                        }
                    }
                ]
            }
        ]
    
    def _replace_placeholders(self, params, doc):
        """
        Replace placeholders in parameters with document values.
        
        Args:
            params (dict): Parameters with placeholders
            doc (object): Document object
            
        Returns:
            dict: Parameters with placeholders replaced
        """
        # Create a copy of params
        new_params = {}
        
        # Replace placeholders in each parameter
        for key, value in params.items():
            if isinstance(value, str):
                # Replace placeholders in string
                for field in doc.meta.fields:
                    if hasattr(doc, field.fieldname):
                        field_value = doc.get(field.fieldname)
                        if field_value is not None:
                            placeholder = f"{{{field.fieldname}}}"
                            value = value.replace(placeholder, str(field_value))
            
            new_params[key] = value
        
        return new_params
    
    def _make_ai_decision(self, action, doc, event, user=None):
        """
        Make an AI-driven decision based on document data.
        
        Args:
            action (dict): AI decision action definition
            doc (object): Document object
            event (str): Event type
            user (str, optional): User who triggered the event
            
        Returns:
            dict: Result of AI decision
        """
        try:
            # Get decision parameters
            decision_type = action.get("decision_type", "classification")
            prompt_template = action.get("prompt_template", "")
            options = action.get("options", [])
            
            # Prepare context
            context = {
                "doctype": doc.doctype,
                "docname": doc.name,
                "event": event,
                "user": user or frappe.session.user
            }
            
            # Add document fields
            doc_fields = {}
            for field in doc.meta.fields:
                if hasattr(doc, field.fieldname):
                    value = doc.get(field.fieldname)
                    if value is not None:
                        doc_fields[field.fieldname] = str(value)
            
            context["document_data"] = doc_fields
            
            # Replace placeholders in prompt template
            for field, value in doc_fields.items():
                placeholder = f"{{{field}}}"
                prompt_template = prompt_template.replace(placeholder, value)
            
            # Build prompt
            if decision_type == "classification":
                prompt = f"{prompt_template}\n\nPlease classify this into one of the following options: {', '.join(options)}.\nResponse:"
            elif decision_type == "extraction":
                prompt = f"{prompt_template}\n\nPlease extract the requested information.\nResponse:"
            else:
                prompt = prompt_template
            
            # Get AI response
            response = self.client.generate_text(prompt)
            
            # Parse response
            parsed_response = self.response_parser.parse_text_response(response)
            
            # Process decision
            decision = parsed_response["content"].strip()
            
            if decision_type == "classification":
                # Find closest match in options
                best_match = None
                best_score = 0
                
                for option in options:
                    if option.lower() in decision.lower():
                        score = len(option)
                        if score > best_score:
                            best_match = option
                            best_score = score
                
                if best_match:
                    decision = best_match
                else:
                    decision = options[0]  # Default to first option
            
            return {
                "decision_type": decision_type,
                "decision": decision,
                "raw_response": parsed_response["content"],
                "tokens_used": response.get("tokens_used", 0)
            }
            
        except Exception as e:
            frappe.log_error(f"Error making AI decision: {str(e)}")
            return {
                "error": str(e),
                "decision": None
            }
    
    def _evaluate_condition(self, action, doc):
        """
        Evaluate a condition on a document.
        
        Args:
            action (dict): Condition action definition
            doc (object): Document object
            
        Returns:
            dict: Result of condition evaluation
        """
        try:
            # Get condition parameters
            field = action.get("field")
            operator = action.get("operator", "equals")
            value = action.get("value")
            
            # Get field value
            if not hasattr(doc, field):
                return {
                    "condition_met": False,
                    "error": f"Field '{field}' not found in document"
                }
            
            field_value = doc.get(field)
            
            # Evaluate condition
            condition_met = False
            
            if operator == "equals":
                condition_met = field_value == value
            elif operator == "not_equals":
                condition_met = field_value != value
            elif operator == "greater_than":
                condition_met = field_value > value
            elif operator == "less_than":
                condition_met = field_value < value
            elif operator == "contains":
                condition_met = value in str(field_value)
            elif operator == "not_contains":
                condition_met = value not in str(field_value)
            elif operator == "is_empty":
                condition_met = not field_value
            elif operator == "is_not_empty":
                condition_met = bool(field_value)
            
            return {
                "condition_met": condition_met,
                "field": field,
                "operator": operator,
                "value": value,
                "field_value": field_value
            }
            
        except Exception as e:
            frappe.log_error(f"Error evaluating condition: {str(e)}")
            return {
                "condition_met": False,
                "error": str(e)
            }
    
    def _log_rule_creation(self, rule):
        """
        Log rule creation to the audit log.
        
        Args:
            rule (dict): Rule definition
        """
        try:
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Rule Creation",
                "details": json.dumps({
                    "rule_name": rule["name"],
                    "doctype": rule["doctype"],
                    "event": rule["event"],
                    "allowed_roles": rule["allowed_roles"],
                    "timestamp": str(now_datetime())
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging rule creation: {str(e)}")
    
    def _log_rule_execution(self, rule, results):
        """
        Log rule execution to the audit log.
        
        Args:
            rule (dict): Rule definition
            results (list): Results of rule execution
        """
        try:
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Rule Execution",
                "details": json.dumps({
                    "rule_name": rule["name"],
                    "doctype": rule["doctype"],
                    "event": rule["event"],
                    "actions_executed": len(results),
                    "timestamp": str(now_datetime())
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging rule execution: {str(e)}")
