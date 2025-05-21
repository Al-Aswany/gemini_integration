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
from ..gemini.exceptions import GeminiAPIError

@frappe.whitelist()
def send_message(conversation_id=None, message=None, context=None):
    """
    Send a message to Gemini and get a response.
    
    Args:
        conversation_id (str, optional): Existing conversation ID
        message (str): User message
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
        
        # Get or create conversation
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
        
        # Build the prompt
        prompt = prompt_builder.build_prompt(
            user_input=message,
            context=context,
            doctype=conversation.context_doctype,
            docname=conversation.context_docname
        )
        
        # Save user message
        user_message = save_message(conversation_id, "User", message)
        
        # Send to Gemini API
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
            "tokens_used": response.get("tokens_used", 0)
        }
        
    except Exception as e:
        frappe.log_error(f"Error in send_message: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_or_create_conversation(conversation_id=None, context=None):
    """
    Get an existing conversation or create a new one.
    
    Args:
        conversation_id (str, optional): Existing conversation ID
        context (dict, optional): Context information for new conversation
        
    Returns:
        object: Frappe document for the conversation
    """
    try:
        # If conversation_id is provided, try to get it
        if conversation_id:
            try:
                conversation = frappe.get_doc("Gemini Conversation", conversation_id)
                return conversation
            except frappe.DoesNotExistError:
                pass
        
        # Create a new conversation
        conversation = frappe.new_doc("Gemini Conversation")
        conversation.session_id = frappe.generate_hash(length=10)
        conversation.user = frappe.session.user
        conversation.start_time = now_datetime()
        conversation.last_updated = now_datetime()
        conversation.status = "Active"
        
        # Add context if provided
        if context and isinstance(context, dict):
            if "doctype" in context:
                conversation.context_doctype = context["doctype"]
                
            if "docname" in context:
                conversation.context_docname = context["docname"]
        
        conversation.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return conversation
        
    except Exception as e:
        frappe.log_error(f"Error in get_or_create_conversation: {str(e)}")
        raise

@frappe.whitelist()
def save_message(conversation_id, role, content, tokens_used=0):
    """
    Save a message to the conversation.
    
    Args:
        conversation_id (str): Conversation ID
        role (str): Message role (User/Assistant)
        content (str): Message content
        tokens_used (int, optional): Tokens used for this message
        
    Returns:
        object: Frappe document for the message
    """
    try:
        message = frappe.new_doc("Gemini Message")
        message.conversation = conversation_id
        message.timestamp = now_datetime()
        message.role = role
        message.content = content
        message.tokens_used = tokens_used
        
        message.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return message
        
    except Exception as e:
        frappe.log_error(f"Error in save_message: {str(e)}")
        raise

@frappe.whitelist()
def get_conversation_history(conversation_id, format_type="text"):
    """
    Get the conversation history.
    
    Args:
        conversation_id (str): Conversation ID
        format_type (str, optional): Format type (text/markdown/html)
        
    Returns:
        str: Formatted conversation history
    """
    try:
        messages = frappe.get_all(
            "Gemini Message",
            filters={"conversation": conversation_id},
            fields=["name", "timestamp", "role", "content"],
            order_by="timestamp asc"
        )
        
        if not messages:
            return ""
        
        # Format the history based on format_type
        if format_type == "html":
            history = "<div class='conversation-history'>"
            for msg in messages:
                role_class = "user" if msg.role == "User" else "assistant"
                history += f"<div class='message {role_class}'>"
                history += f"<div class='role'>{msg.role}</div>"
                history += f"<div class='content'>{msg.content}</div>"
                history += "</div>"
            history += "</div>"
        elif format_type == "markdown":
            history = ""
            for msg in messages:
                history += f"**{msg.role}**: {msg.content}\n\n"
        else:  # text
            history = ""
            for msg in messages:
                history += f"{msg.role}: {msg.content}\n\n"
        
        return history
        
    except Exception as e:
        frappe.log_error(f"Error in get_conversation_history: {str(e)}")
        return ""

@frappe.whitelist()
def submit_feedback(message_id, rating, comments=None):
    """
    Submit feedback for a message.
    
    Args:
        message_id (str): Message ID
        rating (str): Rating (Positive/Negative)
        comments (str, optional): Additional comments
        
    Returns:
        dict: Success status and feedback ID
    """
    try:
        # Validate message exists
        message = frappe.get_doc("Gemini Message", message_id)
        
        # Create feedback
        feedback = frappe.new_doc("Gemini Feedback")
        feedback.message = message_id
        feedback.rating = rating
        feedback.comments = comments
        feedback.user = frappe.session.user
        feedback.timestamp = now_datetime()
        
        feedback.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "feedback_id": feedback.name
        }
        
    except Exception as e:
        frappe.log_error(f"Error in submit_feedback: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_active_conversations():
    """
    Get active conversations for the current user.
    
    Returns:
        list: List of active conversations
    """
    try:
        conversations = frappe.get_all(
            "Gemini Conversation",
            filters={
                "user": frappe.session.user,
                "status": "Active"
            },
            fields=["name", "session_id", "start_time", "last_updated", "context_doctype", "context_docname"],
            order_by="last_updated desc"
        )
        
        # Get the last message for each conversation
        for conv in conversations:
            last_message = frappe.get_all(
                "Gemini Message",
                filters={"conversation": conv.name},
                fields=["content"],
                order_by="timestamp desc",
                limit=1
            )
            
            if last_message:
                conv["last_message"] = last_message[0].content[:100] + "..." if len(last_message[0].content) > 100 else last_message[0].content
            else:
                conv["last_message"] = ""
        
        return conversations
        
    except Exception as e:
        frappe.log_error(f"Error in get_active_conversations: {str(e)}")
        return []

@frappe.whitelist()
def archive_conversation(conversation_id):
    """
    Archive a conversation.
    
    Args:
        conversation_id (str): Conversation ID
        
    Returns:
        dict: Success status
    """
    try:
        frappe.db.set_value("Gemini Conversation", conversation_id, "status", "Archived")
        frappe.db.commit()
        
        return {
            "success": True
        }
        
    except Exception as e:
        frappe.log_error(f"Error in archive_conversation: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
