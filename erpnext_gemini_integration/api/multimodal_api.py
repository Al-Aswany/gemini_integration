# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import now_datetime
from ..gemini.client import GeminiClient
from ..gemini.prompt_builder import PromptBuilder
from ..gemini.response_parser import ResponseParser
from ..utils.context_manager import ContextManager
from ..utils.file_processor import FileProcessor
from ..gemini.exceptions import GeminiAPIError, GeminiFileProcessingError

@frappe.whitelist()
def process_multimodal_request(conversation_id=None, message=None, file_url=None, context=None):
    """
    Process a multimodal request with text and file inputs.
    
    Args:
        conversation_id (str, optional): Existing conversation ID
        message (str): User message
        file_url (str, optional): URL of uploaded file
        context (dict, optional): Additional context information
        
    Returns:
        dict: Response with conversation details and AI message
    """
    try:
        if not message:
            return {
                "success": False,
                "error": "Message is required"
            }
            
        # Parse context if provided as string
        if context and isinstance(context, str):
            try:
                context = json.loads(context)
            except Exception:
                context = {}
        
        # Initialize components
        client = GeminiClient()
        prompt_builder = PromptBuilder()
        response_parser = ResponseParser()
        file_processor = FileProcessor()
        
        # Get or create conversation
        from erpnext_gemini_integration.api.chat_api import get_or_create_conversation, save_message, get_conversation_history
        conversation = get_or_create_conversation(conversation_id, context)
        conversation_id = conversation.name
        
        # Get conversation history
        history = get_conversation_history(conversation_id)
        
        # Add conversation history to context
        if not context:
            context = {}
        context["conversation_history"] = history
        
        # Add current doctype and docname to context if available
        if conversation.context_doctype:
            context["doctype"] = conversation.context_doctype
            
        if conversation.context_docname:
            context["docname"] = conversation.context_docname
        
        # Save user message
        user_message = save_message(conversation_id, "User", message)
        
        # Process file if provided
        images = []
        if file_url:
            file_result = file_processor.process_file(file_url=file_url)
            
            if file_result.get("success"):
                # Check if it's an image
                if file_result.get("file_type") in file_processor.supported_file_types['image']:
                    images.append(file_result.get("file_path"))
                    
                    # Add file info to context
                    context["file_type"] = "image"
                    context["file_info"] = {
                        "type": file_result.get("file_type"),
                        "width": file_result.get("width"),
                        "height": file_result.get("height")
                    }
                else:
                    # For non-image files, add extracted text to prompt
                    text_content = file_result.get("text_content", "")
                    if text_content:
                        message += f"\n\nFile Content:\n{text_content}"
                    
                    # Add file info to context
                    context["file_type"] = "document"
                    context["file_info"] = {
                        "type": file_result.get("file_type"),
                        "size": file_result.get("size")
                    }
        
        # Build the prompt
        prompt = prompt_builder.build_prompt(
            user_input=message,
            context=context,
            doctype=conversation.context_doctype,
            docname=conversation.context_docname
        )
        
        # Send to Gemini API
        if images:
            # Use multimodal endpoint for images
            response = client.generate_multimodal(prompt, images=images)
        else:
            # Use text endpoint for text-only
            response = client.generate_text(prompt)
        
        # Parse the response
        parsed_response = response_parser.parse_text_response(response)
        
        # Save assistant message
        assistant_message = save_message(
            conversation_id, 
            "Assistant", 
            parsed_response["content"],
            response.get("tokens_used", 0)
        )
        
        # Update conversation last_updated
        frappe.db.set_value("Gemini Conversation", conversation_id, "last_updated", now_datetime())
        
        # Return the response
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message_id": assistant_message.name,
            "response": parsed_response["content"],
            "tokens_used": response.get("tokens_used", 0),
            "multimodal": bool(images)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in process_multimodal_request: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def detect_active_context():
    """
    Detect the active context from the current page.
    
    Returns:
        dict: Active context information
    """
    try:
        # Initialize context manager
        context_manager = ContextManager()
        
        # Get active context
        context = context_manager.get_active_doctype_context()
        
        # Log the detection
        _log_context_detection(context)
        
        return {
            "success": True,
            "context": context
        }
        
    except Exception as e:
        frappe.log_error(f"Error detecting active context: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def process_document(doctype, docname, field=None, attachment_name=None):
    """
    Process a document for analysis by Gemini.
    
    Args:
        doctype (str): DocType of the document
        docname (str): Name of the document
        field (str, optional): Field name containing the file
        attachment_name (str, optional): Name of the attachment
        
    Returns:
        dict: Processed document data
    """
    try:
        # Initialize file processor
        file_processor = FileProcessor()
        
        # Process attachment
        result = file_processor.process_attachment(doctype, docname, field, attachment_name)
        
        # Log the processing
        _log_document_processing(doctype, docname, result)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error processing document: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def update_conversation_context(conversation_id, context_data):
    """
    Update the context for a conversation.
    
    Args:
        conversation_id (str): Conversation ID
        context_data (dict or str): New context data
        
    Returns:
        dict: Success status
    """
    try:
        # Parse context if provided as string
        if isinstance(context_data, str):
            try:
                context_data = json.loads(context_data)
            except Exception:
                return {
                    "success": False,
                    "error": "Invalid context data format"
                }
        
        # Initialize context manager
        context_manager = ContextManager()
        
        # Update context
        success = context_manager.update_conversation_context(conversation_id, context_data)
        
        return {
            "success": success
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating conversation context: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def _log_context_detection(context):
    """
    Log context detection to the audit log.
    
    Args:
        context (dict): Detected context
    """
    try:
        # Create a safe copy of context without sensitive data
        safe_context = {
            "context_enabled": context.get("context_enabled", False),
            "has_doctype": "doctype" in context,
            "has_docname": "docname" in context,
            "timestamp": str(now_datetime())
        }
        
        audit_log = frappe.get_doc({
            "doctype": "Gemini Audit Log",
            "timestamp": now_datetime(),
            "user": frappe.session.user,
            "action_type": "Function Call",
            "details": json.dumps({
                "function": "detect_active_context",
                "details": safe_context
            }),
            "status": "Success",
            "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
        })
        
        audit_log.insert(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error logging context detection: {str(e)}")

def _log_document_processing(doctype, docname, result):
    """
    Log document processing to the audit log.
    
    Args:
        doctype (str): DocType of the document
        docname (str): Name of the document
        result (dict): Processing result
    """
    try:
        # Create a safe copy of result without sensitive data
        safe_result = {
            "success": result.get("success", False),
            "file_type": result.get("file_type"),
            "size": result.get("size"),
            "timestamp": str(now_datetime())
        }
        
        audit_log = frappe.get_doc({
            "doctype": "Gemini Audit Log",
            "timestamp": now_datetime(),
            "user": frappe.session.user,
            "action_type": "Function Call",
            "details": json.dumps({
                "function": "process_document",
                "doctype": doctype,
                "docname": docname,
                "details": safe_result
            }),
            "status": "Success" if result.get("success") else "Error",
            "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
        })
        
        audit_log.insert(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error logging document processing: {str(e)}")
