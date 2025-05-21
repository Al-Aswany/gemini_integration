# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import os
import json
import frappe
import google.generativeai as genai
from frappe import _
from frappe.utils import now_datetime
from ..utils.security import mask_sensitive_data
from .exceptions import GeminiAPIError, GeminiRateLimitError, GeminiAuthError

class GeminiClient:
    """
    Core API client for Google's Gemini API with request handling and security measures.
    
    This class handles all communication with the Gemini API, including authentication,
    request formatting, error handling, and response processing.
    """
    
    def __init__(self):
        """Initialize the Gemini client with settings from the database."""
        self.settings = frappe.get_single("Gemini Assistant Settings")
        self.api_key = self.get_api_key()
        self.default_model = self.settings.default_model
        self.rate_limit = self.settings.rate_limits
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
    
    def get_api_key(self):
        """
        Retrieve the API key from settings with proper security measures.
        
        Returns:
            str: The API key for Gemini API
        """
        if not self.settings.api_key:
            frappe.throw(_("Gemini API key not configured. Please set it in Gemini Assistant Settings."))
        
        return self.settings.get_password("api_key")
    
    def generate_text(self, prompt, model=None, safety_settings=None, temperature=0.7, max_tokens=None):
        """
        Generate text response from Gemini API.
        
        Args:
            prompt (str): The prompt to send to Gemini
            model (str, optional): Model to use. Defaults to the configured default model.
            safety_settings (dict, optional): Safety settings for content filtering
            temperature (float, optional): Creativity level. Defaults to 0.7.
            max_tokens (int, optional): Maximum tokens in response
            
        Returns:
            dict: Response from Gemini API with processed content
            
        Raises:
            GeminiAPIError: For general API errors
            GeminiRateLimitError: When rate limits are exceeded
            GeminiAuthError: For authentication issues
        """
        try:
            # Mask sensitive data in prompt
            masked_prompt = mask_sensitive_data(prompt)
            
            # Use default model if not specified
            model_name = model or self.default_model
            
            # Get the model
            model = genai.GenerativeModel(model_name)
            
            # Log the request in audit log
            request_id = self._log_request(masked_prompt, model_name)
            
            # Generate content
            generation_config = {
                "temperature": temperature,
            }
            
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
                
            response = model.generate_content(
                masked_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Process and log the response
            processed_response = self._process_response(response)
            self._log_response(request_id, processed_response)
            
            return processed_response
            
        except genai.RateLimitError as e:
            self._log_error(request_id, str(e), "rate_limit")
            raise GeminiRateLimitError(f"Rate limit exceeded: {str(e)}")
        except genai.AuthError as e:
            self._log_error(request_id, str(e), "auth")
            raise GeminiAuthError(f"Authentication error: {str(e)}")
        except Exception as e:
            self._log_error(request_id, str(e), "general")
            raise GeminiAPIError(f"Error generating content: {str(e)}")
    
    def generate_multimodal(self, prompt, images=None, model=None, safety_settings=None, temperature=0.7, max_tokens=None):
        """
        Generate response from Gemini API with text and image inputs.
        
        Args:
            prompt (str): The text prompt to send to Gemini
            images (list, optional): List of image file paths or URLs
            model (str, optional): Model to use. Defaults to vision model.
            safety_settings (dict, optional): Safety settings for content filtering
            temperature (float, optional): Creativity level. Defaults to 0.7.
            max_tokens (int, optional): Maximum tokens in response
            
        Returns:
            dict: Response from Gemini API with processed content
            
        Raises:
            GeminiAPIError: For general API errors
            GeminiRateLimitError: When rate limits are exceeded
            GeminiAuthError: For authentication issues
        """
        try:
            # Mask sensitive data in prompt
            masked_prompt = mask_sensitive_data(prompt)
            
            # Use vision model if not specified
            model_name = model or "gemini-pro-vision"
            
            # Get the model
            model = genai.GenerativeModel(model_name)
            
            # Prepare content parts
            content_parts = [masked_prompt]
            
            # Add images if provided
            if images and isinstance(images, list):
                for image_path in images:
                    if os.path.exists(image_path):
                        image = genai.types.Image.from_file(image_path)
                        content_parts.append(image)
            
            # Log the request in audit log
            request_id = self._log_request(masked_prompt, model_name, has_images=bool(images))
            
            # Generate content
            generation_config = {
                "temperature": temperature,
            }
            
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
                
            response = model.generate_content(
                content_parts,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Process and log the response
            processed_response = self._process_response(response)
            self._log_response(request_id, processed_response)
            
            return processed_response
            
        except genai.RateLimitError as e:
            self._log_error(request_id, str(e), "rate_limit")
            raise GeminiRateLimitError(f"Rate limit exceeded: {str(e)}")
        except genai.AuthError as e:
            self._log_error(request_id, str(e), "auth")
            raise GeminiAuthError(f"Authentication error: {str(e)}")
        except Exception as e:
            self._log_error(request_id, str(e), "general")
            raise GeminiAPIError(f"Error generating content: {str(e)}")
    
    def _process_response(self, response):
        """
        Process the raw response from Gemini API.
        
        Args:
            response: Raw response from Gemini API
            
        Returns:
            dict: Processed response with text, tokens, and metadata
        """
        try:
            # Extract text content
            text = response.text
            
            # Extract token usage if available
            tokens_used = 0
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
            
            # Build the processed response
            processed_response = {
                "text": text,
                "tokens_used": tokens_used,
                "model": response.model,
                "finish_reason": getattr(response, "finish_reason", "unknown"),
                "raw_response": str(response)
            }
            
            return processed_response
            
        except Exception as e:
            frappe.log_error(f"Error processing Gemini response: {str(e)}")
            return {
                "text": "Error processing response",
                "tokens_used": 0,
                "error": str(e)
            }
    
    def _log_request(self, prompt, model, has_images=False):
        """
        Log the request to the audit log.
        
        Args:
            prompt (str): The prompt sent to Gemini
            model (str): The model used
            has_images (bool): Whether the request included images
            
        Returns:
            str: The request ID for correlation
        """
        try:
            request_id = frappe.generate_hash(length=10)
            
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Query",
                "details": json.dumps({
                    "request_id": request_id,
                    "prompt": prompt,
                    "model": model,
                    "has_images": has_images
                }),
                "status": "Success",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
            return request_id
            
        except Exception as e:
            frappe.log_error(f"Error logging Gemini request: {str(e)}")
            return "error-logging-request"
    
    def _log_response(self, request_id, response):
        """
        Log the response to the audit log.
        
        Args:
            request_id (str): The request ID for correlation
            response (dict): The processed response
        """
        try:
            # Find the existing audit log
            audit_logs = frappe.get_all(
                "Gemini Audit Log",
                filters={"details": ["like", f"%{request_id}%"]},
                limit=1
            )
            
            if not audit_logs:
                return
                
            audit_log = frappe.get_doc("Gemini Audit Log", audit_logs[0].name)
            
            # Update with response details
            details = json.loads(audit_log.details)
            details["response"] = {
                "text_length": len(response.get("text", "")),
                "tokens_used": response.get("tokens_used", 0),
                "finish_reason": response.get("finish_reason", "unknown")
            }
            
            audit_log.details = json.dumps(details)
            audit_log.save(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging Gemini response: {str(e)}")
    
    def _log_error(self, request_id, error_message, error_type):
        """
        Log an error to the audit log.
        
        Args:
            request_id (str): The request ID for correlation
            error_message (str): The error message
            error_type (str): The type of error
        """
        try:
            # Find the existing audit log
            audit_logs = frappe.get_all(
                "Gemini Audit Log",
                filters={"details": ["like", f"%{request_id}%"]},
                limit=1
            )
            
            if audit_logs:
                # Update existing log
                audit_log = frappe.get_doc("Gemini Audit Log", audit_logs[0].name)
                
                details = json.loads(audit_log.details)
                details["error"] = {
                    "message": error_message,
                    "type": error_type
                }
                
                audit_log.details = json.dumps(details)
                audit_log.status = "Error"
                audit_log.save(ignore_permissions=True)
            else:
                # Create new error log
                audit_log = frappe.get_doc({
                    "doctype": "Gemini Audit Log",
                    "timestamp": now_datetime(),
                    "user": frappe.session.user,
                    "action_type": "Query",
                    "details": json.dumps({
                        "request_id": request_id,
                        "error": {
                            "message": error_message,
                            "type": error_type
                        }
                    }),
                    "status": "Error",
                    "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
                })
                
                audit_log.insert(ignore_permissions=True)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging Gemini error: {str(e)}")
