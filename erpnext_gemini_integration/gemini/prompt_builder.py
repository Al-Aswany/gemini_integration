# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import now_datetime

class PromptBuilder:
    """
    Dynamic prompt builder for Gemini API requests.
    
    This class handles the creation of structured prompts for the Gemini API,
    incorporating context, templates, and user inputs while ensuring security
    and consistency.
    """
    
    def __init__(self):
        """Initialize the prompt builder with settings from the database."""
        self.settings = frappe.get_single("Gemini Assistant Settings")
        self.default_templates = self._load_default_templates()
    
    def _load_default_templates(self):
        """
        Load default prompt templates from settings.
        
        Returns:
            dict: Dictionary of template names and their content
        """
        try:
            if self.settings.default_prompt_templates:
                return json.loads(self.settings.default_prompt_templates)
            return {}
        except Exception as e:
            frappe.log_error(f"Error loading prompt templates: {str(e)}")
            return {}
    
    def build_prompt(self, user_input, template_name="general", context=None, doctype=None, docname=None):
        """
        Build a prompt using template and context.
        
        Args:
            user_input (str): The user's input message
            template_name (str, optional): Name of template to use. Defaults to "general".
            context (dict, optional): Additional context variables
            doctype (str, optional): Current doctype context
            docname (str, optional): Current document name context
            
        Returns:
            str: The fully constructed prompt
        """
        # Get the template
        template = self._get_template(template_name)
        
        # Build context dictionary
        context_dict = self._build_context_dict(context, doctype, docname)
        
        # Add system instructions
        prompt = self._add_system_instructions(template)
        
        # Add context information if available
        if context_dict:
            prompt += "\n\n## Context Information:\n"
            for key, value in context_dict.items():
                if key != "conversation_history":
                    prompt += f"{key}: {value}\n"
        
        # Add conversation history if available
        if context_dict and "conversation_history" in context_dict:
            prompt += "\n\n## Conversation History:\n"
            prompt += context_dict["conversation_history"]
        
        # Add user input
        prompt += f"\n\n## User Input:\n{user_input}"
        
        # Log the prompt building (without the full prompt for security)
        self._log_prompt_building(template_name, doctype, docname)
        
        return prompt
    
    def build_analysis_prompt(self, data, analysis_type="general", context=None):
        """
        Build a prompt specifically for data analysis.
        
        Args:
            data (str): The data to analyze
            analysis_type (str, optional): Type of analysis. Defaults to "general".
            context (dict, optional): Additional context variables
            
        Returns:
            str: The fully constructed analysis prompt
        """
        # Get the analysis template
        template = self._get_template("analysis")
        
        # Build context dictionary
        context_dict = self._build_context_dict(context)
        
        # Add system instructions
        prompt = self._add_system_instructions(template)
        
        # Add analysis type
        prompt += f"\n\n## Analysis Type:\n{analysis_type}"
        
        # Add context information if available
        if context_dict:
            prompt += "\n\n## Context Information:\n"
            for key, value in context_dict.items():
                prompt += f"{key}: {value}\n"
        
        # Add data to analyze
        prompt += f"\n\n## Data to Analyze:\n{data}"
        
        # Log the prompt building
        self._log_prompt_building("analysis", analysis_type=analysis_type)
        
        return prompt
    
    def build_document_prompt(self, document_content, operation="summarize", context=None):
        """
        Build a prompt specifically for document operations.
        
        Args:
            document_content (str): The document content
            operation (str, optional): Operation to perform. Defaults to "summarize".
            context (dict, optional): Additional context variables
            
        Returns:
            str: The fully constructed document prompt
        """
        # Get the document template
        template = self._get_template("document_summary")
        
        # Build context dictionary
        context_dict = self._build_context_dict(context)
        
        # Add system instructions
        prompt = self._add_system_instructions(template)
        
        # Add operation type
        prompt += f"\n\n## Operation:\n{operation}"
        
        # Add context information if available
        if context_dict:
            prompt += "\n\n## Context Information:\n"
            for key, value in context_dict.items():
                prompt += f"{key}: {value}\n"
        
        # Add document content
        prompt += f"\n\n## Document Content:\n{document_content}"
        
        # Log the prompt building
        self._log_prompt_building("document", operation=operation)
        
        return prompt
    
    def _get_template(self, template_name):
        """
        Get a prompt template by name.
        
        Args:
            template_name (str): Name of the template
            
        Returns:
            str: The template content or a default template
        """
        if template_name in self.default_templates:
            return self.default_templates[template_name]
        
        # Return a generic template if not found
        return "You are an AI assistant integrated with ERPNext. Provide helpful information based on the context."
    
    def _build_context_dict(self, context=None, doctype=None, docname=None):
        """
        Build a context dictionary from various sources.
        
        Args:
            context (dict, optional): Additional context variables
            doctype (str, optional): Current doctype context
            docname (str, optional): Current document name context
            
        Returns:
            dict: Combined context dictionary
        """
        context_dict = {}
        
        # Add provided context
        if context and isinstance(context, dict):
            context_dict.update(context)
        
        # Add doctype and docname if provided
        if doctype:
            context_dict["current_doctype"] = doctype
        
        if docname:
            context_dict["current_docname"] = docname
            
            # Add document fields if both doctype and docname are provided
            if doctype:
                try:
                    doc = frappe.get_doc(doctype, docname)
                    context_dict["document_fields"] = self._get_safe_doc_fields(doc)
                except Exception as e:
                    frappe.log_error(f"Error getting document fields: {str(e)}")
        
        # Add user information
        context_dict["user"] = frappe.session.user
        
        return context_dict
    
    def _get_safe_doc_fields(self, doc):
        """
        Get document fields with sensitive information masked.
        
        Args:
            doc: Frappe document object
            
        Returns:
            dict: Safe document fields
        """
        from ..utils.security import mask_sensitive_data
        
        # Get all fields
        fields = {}
        for field in doc.meta.fields:
            if hasattr(doc, field.fieldname):
                value = doc.get(field.fieldname)
                if value is not None:
                    # Convert to string and mask sensitive data
                    str_value = str(value)
                    masked_value = mask_sensitive_data(str_value)
                    fields[field.fieldname] = masked_value
        
        return fields
    
    def _add_system_instructions(self, template):
        """
        Add system instructions to the prompt.
        
        Args:
            template (str): The template to use
            
        Returns:
            str: Prompt with system instructions
        """
        prompt = "## System Instructions:\n"
        prompt += template
        return prompt
    
    def _log_prompt_building(self, template_name, doctype=None, docname=None, **kwargs):
        """
        Log the prompt building process to the audit log.
        
        Args:
            template_name (str): Name of the template used
            doctype (str, optional): Current doctype context
            docname (str, optional): Current document name context
            **kwargs: Additional logging information
        """
        try:
            details = {
                "template_name": template_name,
                "timestamp": str(now_datetime())
            }
            
            if doctype:
                details["doctype"] = doctype
            
            if docname:
                details["docname"] = docname
                
            # Add any additional kwargs
            details.update(kwargs)
            
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Function Call",
                "details": json.dumps({
                    "function": "prompt_builder",
                    "details": details
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging prompt building: {str(e)}")
