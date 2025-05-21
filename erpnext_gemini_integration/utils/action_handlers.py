# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import now_datetime

def handle_send_email(params):
    """
    Handle the send_email action.
    
    Args:
        params (dict): Action parameters
        
    Returns:
        dict: Result of action execution
    """
    try:
        # Validate required parameters
        if not params.get("recipients"):
            return {"success": False, "error": "Recipients are required"}
        
        if not params.get("subject"):
            return {"success": False, "error": "Subject is required"}
        
        if not params.get("message"):
            return {"success": False, "error": "Message is required"}
        
        # Get recipients
        recipients = params["recipients"]
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.split(",")]
        
        # Send email
        frappe.sendmail(
            recipients=recipients,
            subject=params["subject"],
            message=params["message"]
        )
        
        return {
            "success": True,
            "message": f"Email sent to {len(recipients)} recipients"
        }
        
    except Exception as e:
        frappe.log_error(f"Error handling send_email action: {str(e)}")
        return {"success": False, "error": str(e)}

def handle_create_task(params):
    """
    Handle the create_task action.
    
    Args:
        params (dict): Action parameters
        
    Returns:
        dict: Result of action execution
    """
    try:
        # Validate required parameters
        if not params.get("subject"):
            return {"success": False, "error": "Subject is required"}
        
        # Create task
        task = frappe.new_doc("Task")
        task.subject = params["subject"]
        
        if params.get("description"):
            task.description = params["description"]
        
        if params.get("assigned_to"):
            task.assigned_to = params["assigned_to"]
        
        task.insert()
        
        return {
            "success": True,
            "task": task.name,
            "message": f"Task '{task.name}' created successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error handling create_task action: {str(e)}")
        return {"success": False, "error": str(e)}

def handle_update_document(params):
    """
    Handle the update_document action.
    
    Args:
        params (dict): Action parameters
        
    Returns:
        dict: Result of action execution
    """
    try:
        # Validate required parameters
        if not params.get("doctype"):
            return {"success": False, "error": "DocType is required"}
        
        if not params.get("docname"):
            return {"success": False, "error": "Document name is required"}
        
        if not params.get("fields"):
            return {"success": False, "error": "Fields to update are required"}
        
        # Get document
        doc = frappe.get_doc(params["doctype"], params["docname"])
        
        # Update fields
        fields = params["fields"]
        for field, value in fields.items():
            if hasattr(doc, field):
                doc.set(field, value)
        
        # Save document
        doc.save()
        
        return {
            "success": True,
            "message": f"Document {params['doctype']} {params['docname']} updated successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error handling update_document action: {str(e)}")
        return {"success": False, "error": str(e)}

def handle_create_document(params):
    """
    Handle the create_document action.
    
    Args:
        params (dict): Action parameters
        
    Returns:
        dict: Result of action execution
    """
    try:
        # Validate required parameters
        if not params.get("doctype"):
            return {"success": False, "error": "DocType is required"}
        
        if not params.get("fields"):
            return {"success": False, "error": "Fields are required"}
        
        # Create document
        doc = frappe.new_doc(params["doctype"])
        
        # Set fields
        fields = params["fields"]
        for field, value in fields.items():
            if hasattr(doc, field):
                doc.set(field, value)
        
        # Insert document
        doc.insert()
        
        return {
            "success": True,
            "docname": doc.name,
            "message": f"Document {params['doctype']} {doc.name} created successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error handling create_document action: {str(e)}")
        return {"success": False, "error": str(e)}

def handle_generate_report(params):
    """
    Handle the generate_report action.
    
    Args:
        params (dict): Action parameters
        
    Returns:
        dict: Result of action execution
    """
    try:
        # Validate required parameters
        if not params.get("report_name"):
            return {"success": False, "error": "Report name is required"}
        
        # Get report
        report_name = params["report_name"]
        filters = params.get("filters", {})
        
        # Generate report
        report = frappe.get_doc("Report", report_name)
        
        if report.report_type == "Query Report":
            # For query reports
            result = frappe.desk.query_report.run(
                report_name,
                filters=filters,
                user=frappe.session.user
            )
        else:
            # For script reports
            result = report.execute_script_report(filters)
        
        return {
            "success": True,
            "report": report_name,
            "data": result
        }
        
    except Exception as e:
        frappe.log_error(f"Error handling generate_report action: {str(e)}")
        return {"success": False, "error": str(e)}

def handle_process_purchase_order(params):
    """
    Handle the process_purchase_order action.
    
    This is an example of integration with ERPNext Purchase Order process.
    
    Args:
        params (dict): Action parameters
        
    Returns:
        dict: Result of action execution
    """
    try:
        # Validate required parameters
        if not params.get("purchase_order"):
            return {"success": False, "error": "Purchase Order is required"}
        
        # Get Purchase Order
        po_name = params["purchase_order"]
        po = frappe.get_doc("Purchase Order", po_name)
        
        # Check action to perform
        action = params.get("action", "submit")
        
        if action == "submit":
            # Submit Purchase Order
            if po.docstatus == 0:
                po.submit()
                return {
                    "success": True,
                    "message": f"Purchase Order {po_name} submitted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Purchase Order {po_name} is already submitted or cancelled"
                }
                
        elif action == "create_receipt":
            # Create Purchase Receipt
            from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_receipt
            
            if po.docstatus == 1:
                pr = make_purchase_receipt(po_name)
                pr.insert()
                
                return {
                    "success": True,
                    "purchase_receipt": pr.name,
                    "message": f"Purchase Receipt {pr.name} created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Purchase Order {po_name} must be submitted to create receipt"
                }
                
        elif action == "create_invoice":
            # Create Purchase Invoice
            from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import make_purchase_invoice
            
            if po.docstatus == 1:
                pi = make_purchase_invoice(po_name)
                pi.insert()
                
                return {
                    "success": True,
                    "purchase_invoice": pi.name,
                    "message": f"Purchase Invoice {pi.name} created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Purchase Order {po_name} must be submitted to create invoice"
                }
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
        
    except Exception as e:
        frappe.log_error(f"Error handling process_purchase_order action: {str(e)}")
        return {"success": False, "error": str(e)}

def handle_process_sales_order(params):
    """
    Handle the process_sales_order action.
    
    This is an example of integration with ERPNext Sales Order process.
    
    Args:
        params (dict): Action parameters
        
    Returns:
        dict: Result of action execution
    """
    try:
        # Validate required parameters
        if not params.get("sales_order"):
            return {"success": False, "error": "Sales Order is required"}
        
        # Get Sales Order
        so_name = params["sales_order"]
        so = frappe.get_doc("Sales Order", so_name)
        
        # Check action to perform
        action = params.get("action", "submit")
        
        if action == "submit":
            # Submit Sales Order
            if so.docstatus == 0:
                so.submit()
                return {
                    "success": True,
                    "message": f"Sales Order {so_name} submitted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Sales Order {so_name} is already submitted or cancelled"
                }
                
        elif action == "create_delivery":
            # Create Delivery Note
            from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
            
            if so.docstatus == 1:
                dn = make_delivery_note(so_name)
                dn.insert()
                
                return {
                    "success": True,
                    "delivery_note": dn.name,
                    "message": f"Delivery Note {dn.name} created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Sales Order {so_name} must be submitted to create delivery note"
                }
                
        elif action == "create_invoice":
            # Create Sales Invoice
            from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
            
            if so.docstatus == 1:
                si = make_sales_invoice(so_name)
                si.insert()
                
                return {
                    "success": True,
                    "sales_invoice": si.name,
                    "message": f"Sales Invoice {si.name} created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Sales Order {so_name} must be submitted to create invoice"
                }
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
        
    except Exception as e:
        frappe.log_error(f"Error handling process_sales_order action: {str(e)}")
        return {"success": False, "error": str(e)}
