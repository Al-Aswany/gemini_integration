# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import json
import re
from frappe import _
from frappe.utils import now_datetime

class ResponseParser:
    """
    Response parser for Gemini API responses.
    
    This class handles the parsing, formatting, and extraction of structured data
    from Gemini API responses, ensuring consistent output formats and proper error handling.
    """
    
    def __init__(self):
        """Initialize the response parser."""
        pass
    
    def parse_text_response(self, response, format_type="markdown"):
        """
        Parse a text response from Gemini API.
        
        Args:
            response (dict): The response from Gemini API
            format_type (str, optional): Output format type. Defaults to "markdown".
            
        Returns:
            dict: Parsed and formatted response
        """
        try:
            # Extract the text content
            text = response.get("text", "")
            
            # Format based on requested type
            if format_type == "html":
                formatted_text = self._convert_to_html(text)
            elif format_type == "plain":
                formatted_text = self._convert_to_plain(text)
            else:  # Default to markdown
                formatted_text = text
            
            # Build the parsed response
            parsed_response = {
                "content": formatted_text,
                "format": format_type,
                "tokens_used": response.get("tokens_used", 0),
                "success": True
            }
            
            # Log the parsing
            self._log_parsing(response, parsed_response)
            
            return parsed_response
            
        except Exception as e:
            frappe.log_error(f"Error parsing text response: {str(e)}")
            return {
                "content": "Error parsing response",
                "format": format_type,
                "tokens_used": response.get("tokens_used", 0),
                "success": False,
                "error": str(e)
            }
    
    def extract_structured_data(self, response, expected_format=None):
        """
        Extract structured data from a response.
        
        Args:
            response (dict): The response from Gemini API
            expected_format (str, optional): Expected data format (json, csv, etc.)
            
        Returns:
            dict: Extracted structured data
        """
        try:
            # Extract the text content
            text = response.get("text", "")
            
            # Try to extract JSON data
            json_data = self._extract_json(text)
            if json_data and (expected_format is None or expected_format == "json"):
                return {
                    "data": json_data,
                    "format": "json",
                    "tokens_used": response.get("tokens_used", 0),
                    "success": True
                }
            
            # Try to extract CSV data
            if expected_format == "csv":
                csv_data = self._extract_csv(text)
                if csv_data:
                    return {
                        "data": csv_data,
                        "format": "csv",
                        "tokens_used": response.get("tokens_used", 0),
                        "success": True
                    }
            
            # If no structured data found, return the raw text
            return {
                "data": text,
                "format": "text",
                "tokens_used": response.get("tokens_used", 0),
                "success": True,
                "note": "No structured data found in expected format"
            }
            
        except Exception as e:
            frappe.log_error(f"Error extracting structured data: {str(e)}")
            return {
                "data": None,
                "format": "unknown",
                "tokens_used": response.get("tokens_used", 0),
                "success": False,
                "error": str(e)
            }
    
    def extract_action_items(self, response):
        """
        Extract action items from a response.
        
        Args:
            response (dict): The response from Gemini API
            
        Returns:
            dict: Extracted action items
        """
        try:
            # Extract the text content
            text = response.get("text", "")
            
            # Look for action items in various formats
            actions = []
            
            # Pattern 1: Numbered or bulleted lists with action verbs
            action_pattern = r'(?:^|\n)(?:\d+\.|\*|\-)\s+((?:[A-Z][a-z]+|[A-Z]+)(?:\s+[a-z]+)+)'
            action_matches = re.findall(action_pattern, text)
            
            for match in action_matches:
                # Check if it starts with an action verb
                if self._is_action_verb(match.split()[0]):
                    actions.append(match.strip())
            
            # Pattern 2: Lines starting with "Action:" or similar
            action_header_pattern = r'(?:^|\n)(?:Action|TODO|Task)(?:s)?(?:\:|\s+\-\s+)(.*?)(?:\n|$)'
            action_header_matches = re.findall(action_header_pattern, text, re.IGNORECASE)
            
            for match in action_header_matches:
                actions.append(match.strip())
            
            # Return the extracted actions
            return {
                "actions": actions,
                "count": len(actions),
                "tokens_used": response.get("tokens_used", 0),
                "success": True
            }
            
        except Exception as e:
            frappe.log_error(f"Error extracting action items: {str(e)}")
            return {
                "actions": [],
                "count": 0,
                "tokens_used": response.get("tokens_used", 0),
                "success": False,
                "error": str(e)
            }
    
    def _convert_to_html(self, markdown_text):
        """
        Convert markdown text to HTML.
        
        Args:
            markdown_text (str): Text in markdown format
            
        Returns:
            str: HTML formatted text
        """
        try:
            import markdown
            return markdown.markdown(markdown_text)
        except ImportError:
            # Fallback to basic conversion if markdown module is not available
            html = markdown_text
            # Convert headers
            html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            
            # Convert bold and italic
            html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
            
            # Convert lists
            html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
            html = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\g<0></ul>', html, flags=re.DOTALL)
            
            # Convert paragraphs
            html = re.sub(r'(?<!\n)\n(?!\n)', r'<br>', html)
            html = re.sub(r'\n\n', r'</p>\n\n<p>', html)
            html = '<p>' + html + '</p>'
            
            return html
    
    def _convert_to_plain(self, markdown_text):
        """
        Convert markdown text to plain text.
        
        Args:
            markdown_text (str): Text in markdown format
            
        Returns:
            str: Plain text
        """
        # Remove headers
        plain = re.sub(r'^#{1,6}\s+(.*?)$', r'\1', markdown_text, flags=re.MULTILINE)
        
        # Remove bold and italic
        plain = re.sub(r'\*\*(.*?)\*\*', r'\1', plain)
        plain = re.sub(r'\*(.*?)\*', r'\1', plain)
        
        # Convert lists to simple text
        plain = re.sub(r'^- (.*?)$', r'• \1', plain, flags=re.MULTILINE)
        
        return plain
    
    def _extract_json(self, text):
        """
        Extract JSON data from text.
        
        Args:
            text (str): Text that may contain JSON
            
        Returns:
            dict or None: Extracted JSON data or None if not found
        """
        # Look for JSON pattern
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, text)
        
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON without code blocks
        try:
            # Look for text that starts with { and ends with }
            json_pattern = r'(\{[\s\S]*\})'
            json_match = re.search(json_pattern, text)
            
            if json_match:
                return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _extract_csv(self, text):
        """
        Extract CSV data from text.
        
        Args:
            text (str): Text that may contain CSV
            
        Returns:
            list or None: Extracted CSV data as list of lists or None if not found
        """
        # Look for CSV pattern
        csv_pattern = r'```csv\s*([\s\S]*?)\s*```'
        csv_match = re.search(csv_pattern, text)
        
        if csv_match:
            csv_text = csv_match.group(1)
        else:
            # Try to find CSV-like content without code blocks
            lines = text.split('\n')
            csv_lines = []
            
            # Look for lines with consistent delimiter patterns
            for line in lines:
                if ',' in line and line.count(',') > 0:
                    csv_lines.append(line)
            
            if len(csv_lines) > 1:
                csv_text = '\n'.join(csv_lines)
            else:
                return None
        
        # Parse CSV
        import csv
        from io import StringIO
        
        csv_data = []
        csv_file = StringIO(csv_text)
        csv_reader = csv.reader(csv_file)
        
        for row in csv_reader:
            csv_data.append(row)
        
        return csv_data if csv_data else None
    
    def _is_action_verb(self, word):
        """
        Check if a word is an action verb.
        
        Args:
            word (str): Word to check
            
        Returns:
            bool: True if it's an action verb
        """
        action_verbs = [
            "Create", "Update", "Delete", "Add", "Remove", "Modify",
            "Check", "Verify", "Review", "Analyze", "Implement",
            "Deploy", "Test", "Debug", "Fix", "Resolve", "Send",
            "Receive", "Configure", "Setup", "Install", "Uninstall",
            "Enable", "Disable", "Start", "Stop", "Restart",
            "Backup", "Restore", "Archive", "Extract", "Compile"
        ]
        
        return word in action_verbs
    
    def _log_parsing(self, original_response, parsed_response):
        """
        Log the response parsing to the audit log.
        
        Args:
            original_response (dict): The original response
            parsed_response (dict): The parsed response
        """
        try:
            details = {
                "original_format": original_response.get("format", "unknown"),
                "parsed_format": parsed_response.get("format", "unknown"),
                "tokens_used": original_response.get("tokens_used", 0),
                "success": parsed_response.get("success", False),
                "timestamp": str(now_datetime())
            }
            
            audit_log = frappe.get_doc({
                "doctype": "Gemini Audit Log",
                "timestamp": now_datetime(),
                "user": frappe.session.user,
                "action_type": "Function Call",
                "details": json.dumps({
                    "function": "response_parser",
                    "details": details
                }),
                "status": "Success" if parsed_response.get("success", False) else "Error",
                "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
            })
            
            audit_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error logging response parsing: {str(e)}")
