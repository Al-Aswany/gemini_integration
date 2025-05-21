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

class WorkflowEngine:
    """
    Workflow automation engine for Gemini integration.
    
    This class provides methods for automating workflows based on document events,
    user actions, and AI-driven decision making.
    """
    
    def __init__(self):
        """Initialize the workflow engine."""
        self.settings = frappe.get_single("Gemini Assistant Settings")
        self.client = GeminiClient()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
    
    def process_document_event(self, doctype, docname, event, user=None):
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
            # Check if workflow automation is enabled
            if not self.settings.enable_workflow_automation:
                return {"success": False, "message": "Workflow automation is disabled"}
            
            # Get document
            doc = frappe.get_doc(doctype, docname)
            
            # Get applicable workflows
            workflows = self._get_applicable_workflows(doctype, event)
            
            if not workflows:
                return {"success": True, "message": "No applicable workflows found"}
            
            # Process each workflow
            results = []
            for workflow in workflows:
                result = self._execute_workflow(workflow, doc, event, user)
                results.append(result)
            
            # Log the workflow execution
            self._log_workflow_execution(doctype, docname, event, results)
            
            return {
                "success": True,
                "workflows_executed": len(results),
                "results": results
            }
            
        except Exception as e:
            frappe.log_error(f"Error processing document event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def execute_custom_action(self, action_name, params=None, user=None):
        """
        Execute a custom action defined in the system.
        
        Args:
            action_name (str): Name of the custom action
            params (dict, optional): Parameters for the action
            user (str, optional): User executing the action
            
        Returns:
            dict: Result of action execution
        """
        try:
            # Check if workflow automation is enabled
            if not self.settings.enable_workflow_automation:
                return {"success": False, "message": "Workflow automation is disabled"}
            
            # Get action definition
            action = self._get_action_definition(action_name)
            
            if not action:
                return {"success": False, "error": f"Action '{action_name}' not found"}
            
            # Check permissions
            if not self._check_action_permissions(action, user or frappe.session.user):
                return {"success": False, "error": "Permission denied"}
            
            # Execute the action
            result = self._execute_action(action, params)
            
            # Log the action execution
            self._log_action_execution(action_name, params, result)
            
            return result
            
        except Exception as e:
            frappe.log_error(f"Error executing custom action: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_ai_recommendation(self, doctype, docname, context=None):
        """
        Get AI recommendations for a document.
        
        Args:
            doctype (str): DocType of the document
            docname (str): Name of the document
            context (dict, optional): Additional context
            
        Returns:
            dict: AI recommendations
        """
        try:
            # Check if workflow automation is enabled
            if not self.settings.enable_workflow_automation:
                return {"success": False, "message": "Workflow automation is disabled"}
            
            # Get document
            doc = frappe.get_doc(doctype, docname)
            
            # Prepare context
            if not context:
                context = {}
                
            context["doctype"] = doctype
            context["docname"] = docname
            
            # Add document fields
            doc_fields = {}
            for field in doc.meta.fields:
                if hasattr(doc, field.fieldname):
                    value = doc.get(field.fieldname)
                    if value is not None:
                        doc_fields[field.fieldname] = str(value)
            
            context["document_data"] = doc_fields
            
            # Build prompt for recommendations
            prompt = self.prompt_builder.build_prompt(
                user_input=f"Please provide recommendations for this {doctype} document.",
                context=context,
                doctype=doctype,
                docname=docname
            )
            
            # Get AI response
            response = self.client.generate_text(prompt)
            
            # Parse response
            parsed_response = self.response_parser.parse_text_response(response)
            
            # Log the recommendation
            self._log_ai_recommendation(doctype, docname, parsed_response)
            
            return {
                "success": True,
                "recommendations": parsed_response["content"],
                "tokens_used": response.get("tokens_used", 0)
            }
            
        except Exception as e:
            frappe.log_error(f"Error getting AI recommendation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_applicable_workflows(self, doctype, event):
        """
        Get workflows applicable to a doctype and event.
        
        Args:
            doctype (str): DocType
            event (str): Event type
            
        Returns:
            list: List of applicable workflows
        """
        # This would typically query a custom DocType for workflow definitions
        # For now, we'll return a hardcoded example
        return [
            {
                "name": "example_workflow",
                "doctype": doctype,
                "event": event,
                "actions": [
                    {
                        "type": "notification",
                        "recipients": ["Administrator"],
                        "subject": f"Document {doctype} event: {event}",
                        "message": f"The document {doctype} has triggered event {event}."
                    }
                ]
            }
        ]
    
    def _execute_workflow(self, workflow, doc, event, user=None):
        """
        Execute a workflow on a document.
        
        Args:
            workflow (dict): Workflow definition
            doc (object): Document object
            event (str): Event type
            user (str, optional): User who triggered the event
            
        Returns:
            dict: Result of workflow execution
        """
        try:
            results = []
            
            # Execute each action in the workflow
            for action in workflow.get("actions", []):
                action_type = action.get("type")
                
                if action_type == "notification":
                    # Send notification
                    result = self._send_notification(
                        recipients=action.get("recipients", []),
                        subject=action.get("subject", ""),
                        message=action.get("message", ""),
                        doc=doc
                    )
                    results.append({"type": "notification", "result": result})
                
                elif action_type == "update_field":
                    # Update document field
                    field = action.get("field")
                    value = action.get("value")
                    
                    if field and hasattr(doc, field):
                        doc.set(field, value)
                        doc.save()
                        results.append({"type": "update_field", "field": field, "value": value})
                
                elif action_type == "create_document":
                    # Create new document
                    new_doctype = action.get("doctype")
                    fields = action.get("fields", {})
                    
                    new_doc = frappe.new_doc(new_doctype)
                    for field, value in fields.items():
                        new_doc.set(field, value)
                    
                    new_doc.insert()
                    results.append({"type": "create_document", "doctype": new_doctype, "name": new_doc.name})
                
                elif action_type == "custom_action":
                    # Execute custom action
                    action_name = action.get("action_name")
                    params = action.get("params", {})
                    
                    result = self.execute_custom_action(action_name, params, user)
                    results.append({"type": "custom_action", "action": action_name, "result": result})
            
            return {
                "workflow": workflow.get("name"),
                "success": True,
                "actions_executed": len(results),
                "results": results
            }
            
        except Exception as e:
            frappe.log_error(f"Error executing workflow: {str(e)}")
            return {
                "workflow": workflow.get("name"),
                "success": False,
                "error": str(e)
            }
    
    def _get_action_definition(self, action_name):
        """
        Get the definition of a custom action.
        
        Args:
            action_name (str): Name of the custom action
            
        Returns:
            dict: Action definition
        """
        # This would typically query a custom DocType for action definitions
        # For now, we'll return a hardcoded example
        actions = {
            "send_email": {
                "name": "send_email",
                "description": "Send an email to specified recipients",
                "allowed_roles": ["System Manager", "Administrator"],
                "parameters": ["recipients", "subject", "message"]
            },
            "create_task": {
                "name": "create_task",
                "description": "Create a new task",
                "allowed_roles": ["System Manager", "Administrator"],
                "parameters": ["subject", "description", "assigned_to"]
            }
        }
        
        return actions.get(action_name)
    
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
    
    def _execute_action(self, action, params):
        """
        Execute a custom action.
        
        Args:
            action (dict): Action definition
            params (dict): Action parameters
            
        Returns:
            dict: Result of action execution
        """
        action_name = action.get("name")
        
        if action_name == "send_email":
            # Send email
            return self._send_email(
                recipients=params.get("recipients", []),
                subject=params.get("subject", ""),
                message=params.get("message", "")
            )
        
        elif action_name == "create_task":
            # Create task
            return self._create_task(
                subject=params.get("subject", ""),
                description=params.get("description", ""),
                assigned_to=params.get("assigned_to")
            )
        
        return {"success": False, "error": f"Unknown action: {action_name}"}
    
    def _send_notification(self, recipients, subject, message, doc=None):
        """
        Send a notification to users.
        
        Args:
            recipients (list): List of recipient users
            subject (str): Notification subject
            message (str): Notification message
            doc (object, optional): Related document
            
        Returns:
            dict: Result of notification sending
        """
        try:
            # Replace placeholders in message
            if doc:
                for field in doc.meta.fields:
                    if hasattr(doc, field.fieldname):
                        value = doc.get(field.fieldname)
                        if value is not None:
                            placeholder = f"{{{field.fieldname}}}"
                            message = message.replace(placeholder, str(value))
            
            # Send notification to each recipient
            for user in recipients:
                frappe.publish_realtime(
                    event="eval_js",
                    message=f'frappe.show_alert({{message: "{message}", indicator: "blue"}});',
                    user=user
                )
            
            return {"success": True, "recipients": len(recipients)}
            
        except Exception as e:
            frappe.log_error(f"Error sending notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _send_email(self, recipients, subject, message):
        """
        Send an email.
        
        Args:
            recipients (list): List of recipient email addresses
            subject (str): Email subject
            message (str): Email message
            
        Returns:
            dict: Result of email sending
        """
        try:
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=message
            )
            
            return {"success": True, "recipients": len(recipients)}
            
        except Exception as e:
            frappe.log_error(f"Error sending email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_task(self, subject, description, assigned_to=None):
        """
        Create a new task.
        
        Args:
            subject (str): Task subject
            description (str): Task description
            assigned_to (str, optional): User to assign the task to
            
        Returns:
            dict: Result of task creation
        """
        try:
            task = frappe.new_doc("Task")
            task.subject = subject
            task.description = description
            
            if assigned_to:
                task.assigned_to = assigned_to
            
            task.insert()
            
            return {"success": True, "task": task.name}
            
        except Exception as e:
            frappe.log_error(f"Error creating task: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _log_workflow_execution(self, doctype, docname, event, results):
        """
        Log workflow execution to the audit log.
        
        Args:
            doctype (str): DocType of the document
            docname (str): Name of the document
            event (str): Event type
            results (list): Results of workflow execution
        """
        try:
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Workflow",
                "details": json.dumps({
                    "doctype": doctype,
                    "docname": docname,
                    "event": event,
                    "workflows_executed": len(results),
                    "timestamp": str(now_datetime())
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging workflow execution: {str(e)}")
    
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
                "action_type": "Custom Action",
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
    
    def _log_ai_recommendation(self, doctype, docname, recommendation):
        """
        Log AI recommendation to the audit log.
        
        Args:
            doctype (str): DocType of the document
            docname (str): Name of the document
            recommendation (dict): AI recommendation
        """
        try:
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "AI Recommendation",
                "details": json.dumps({
                    "doctype": doctype,
                    "docname": docname,
                    "recommendation_length": len(recommendation.get("content", "")),
                    "timestamp": str(now_datetime())
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging AI recommendation: {str(e)}")
