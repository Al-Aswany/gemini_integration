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
from ..gemini.langchain_sql_handler import text_to_sql_with_results, initialize_sql_chain
from ..utils.visualization import generate_visualization

@frappe.whitelist()
def send_message(conversation_id=None, message=None, context=None):
    """
    Send a message to Gemini and get a response.
    If message starts with "QueryDB: ", it's treated as a Text-to-SQL query.
    
    Args:
        conversation_id (str, optional): Existing conversation ID
        message (str): User message
        context (dict, optional): Additional context information
        
    Returns:
        dict: Response with conversation details and AI message or SQL results
    """
    try:
        if not message:
            return {"success": False, "error": "Message is required"}

        # Initialize LangChain components (especially schema) on first API call if not already done.
        # This is a simple way to ensure it's ready. A more robust solution might use hooks.py on app load.
        try:
            initialize_sql_chain()
        except Exception as e:
            frappe.log_error(f"Failed to initialize LangChain SQL Chain: {str(e)}")
            # Depending on policy, we might want to prevent queries if this fails.
            # For now, general chat might still work.

        if message.strip().upper().startswith("QUERYDB:"):
            user_query = message.strip()[len("QUERYDB:"):].strip()
            if not user_query:
                return {"success": False, "error": "Query cannot be empty after 'QueryDB: ' prefix."}

            sql_result_data = text_to_sql_with_results(user_query)

            # Log user message (as a query)
            conversation = get_or_create_conversation(conversation_id, context)
            conversation_id = conversation.name
            save_message(conversation_id, "User", f"QueryDB: {user_query}")


            if "error" in sql_result_data:
                # Log assistant error response (containing the SQL error)
                save_message(conversation_id, "Assistant", f"Error processing your query: {sql_result_data['error']}")
                return {
                    "success": False,
                    "conversation_id": conversation_id,
                    "response_type": "sql_error",
                    "error_details": sql_result_data,
                    "response": f"Sorry, I encountered an error trying to answer your question: {sql_result_data['error']}"
                }
            
            else: # Successfully got SQL results
                visualization_output = None
                try:
                    # Assuming sql_result_data["results"] is List[Dict]
                    # And sql_result_data["natural_query"] and sql_result_data["generated_sql"] exist
                    if sql_result_data.get("results"):
                        visualization_output = generate_visualization(
                            data=sql_result_data["results"],
                            natural_query=sql_result_data.get("natural_query", user_query),
                            generated_sql=sql_result_data.get("generated_sql", "N/A")
                            # requested_chart_type can be passed if parsed from user_query
                        )
                except Exception as vis_ex:
                    frappe.log_error(f"Error during visualization generation: {str(vis_ex)}")
                    visualization_output = {"type": "message", "content": "Could not generate visualization."}

                assistant_response_summary = f"Generated SQL: {sql_result_data.get('generated_sql', 'N/A')}\nResults fetched."
                if sql_result_data.get('has_more_results'):
                    assistant_response_summary += "\n(Showing a subset of results. More data is available.)"
                if visualization_output and visualization_output["type"] == "message":
                    assistant_response_summary += f"\nVisualization: {visualization_output['content']}"
                elif visualization_output and visualization_output["type"] != "message":
                        assistant_response_summary += "\nVisualization generated."

                save_message(conversation_id, "Assistant", assistant_response_summary)
                frappe.db.set_value("Gemini Conversation", conversation_id, "last_updated", frappe.utils.now_datetime())

                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "response_type": "sql_query_result",
                    "data": sql_result_data,
                    "visualization": visualization_output, # Add visualization here
                    "response": f"I've processed your database query. See data and visualization for details."
                }
        else: # Existing general chat logic
            # Parse context if provided as string
            if context and isinstance(context, str):
                try:
                    context = json.loads(context)
                except Exception:
                    context = {} # Default to empty if malformed
            
            client = GeminiClient()
            prompt_builder = PromptBuilder()
            response_parser = ResponseParser()

            conversation = get_or_create_conversation(conversation_id, context)
            conversation_id = conversation.name

            history = get_conversation_history(conversation_id)

            current_context = context if context else {}
            current_context["conversation_history"] = history

            if conversation.context_doctype:
                current_context["doctype"] = conversation.context_doctype
            if conversation.context_docname:
                current_context["docname"] = conversation.context_docname

            prompt = prompt_builder.build_prompt(
                user_input=message,
                context=current_context,
                doctype=conversation.context_doctype,
                docname=conversation.context_docname
            )

            save_message(conversation_id, "User", message)

            # API Call to Gemini (non-SQL)
            gemini_response_data = client.generate_text(prompt) # Assuming this returns a dict like {"text": "...", "tokens_used": ...}

            # The GeminiClient's generate_text returns a dict with a "text" key for the content
            ai_content = gemini_response_data.get("text", "Sorry, I could not process that.")
            tokens_used = gemini_response_data.get("tokens_used", 0)

            assistant_message_doc = save_message(conversation_id, "Assistant", ai_content, tokens_used)

            frappe.db.set_value("Gemini Conversation", conversation_id, "last_updated", frappe.utils.now_datetime())

            return {
                "success": True,
                "conversation_id": conversation_id,
                "message_id": assistant_message_doc.name,
                "response_type": "chat",
                "response": ai_content,
                "tokens_used": tokens_used
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error in send_message API: {str(e)}")
        # Ensure conversation_id is available if an error occurs mid-process
        # This might not always be set if error is very early.
        conv_id_for_error = conversation_id if 'conversation_id' in locals() and conversation_id else None
        return {
            "success": False,
            "error": str(e),
            "conversation_id": conv_id_for_error,
            "response_type": "general_error"
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
