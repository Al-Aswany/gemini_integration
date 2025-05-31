# -*- coding: utf-8 -*-
# Copyright (c) 2025, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# Cache key for storing the schema
SCHEMA_CACHE_KEY = "erpnext_gemini_integration_db_schema"
# Cache timeout in seconds (e.g., 1 hour)
SCHEMA_CACHE_TIMEOUT = 3600

def get_table_columns(table_name):
    """
    Fetches column names and their data types for a given table.
    Uses information_schema for compatibility, assuming PostgreSQL or MariaDB/MySQL.
    """
    columns_info = []

    # Note: Frappe's db_type can be 'mariadb' or 'postgres'
    # The query for information_schema is slightly different for column data types.

    # Default to a generic query, specific adjustments might be needed
    # For PostgreSQL: data_type
    # For MariaDB/MySQL: COLUMN_TYPE
    # This example tries a common way, but might need refinement based on exact DB.

    # Simplified query - might need more specific type introspection
    try:
        # frappe.db.escape is important for table_name if it could come from unsafe source,
        # but here it's generated internally from `show tables` or `information_schema.tables`
        # so it should be safe.
        cols = frappe.db.sql(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """, as_dict=True)

        for col in cols:
            columns_info.append({"name": col.column_name, "type": col.data_type})

    except Exception as e:
        frappe.log_error(f"Error fetching schema for table {table_name}: {str(e)}",
                         "DB Schema Introspection Error")
        # Fallback or re-raise, depending on desired robustness
        # For now, just return empty if error, to not break entire schema process
        return []

    return columns_info

def _fetch_schema_from_db():
    """
    Fetches the schema for all 'tab%' tables from the database.
    """
    schema = {}
    try:
        # Get all table names starting with 'tab'
        # This query is for MySQL/MariaDB. For PostgreSQL: SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'tab%';
        # Frappe's frappe.db.get_tables() might be a more abstract way if available and suitable.

        # Using frappe.db.get_tables() is preferred as it's DB agnostic
        tables = frappe.db.get_tables()

        tab_tables = [table for table in tables if table.startswith("tab")]

        for table_name in tab_tables:
            # Removing 'tab' prefix for a cleaner name if desired, but LangChain might expect full name
            # For now, keep full name.
            clean_name = table_name # table_name[3:]
            columns = get_table_columns(table_name)
            if columns: # Only add if we got column info
                schema[clean_name] = columns

        if not schema:
            frappe.log_error("No tables starting with 'tab' found or failed to fetch schema for all.",
                             "DB Schema Introspection Warning")

    except Exception as e:
        frappe.log_error(f"Failed to fetch database schema: {str(e)}",
                         "DB Schema Introspection Error")
        return {} # Return empty schema on major failure

    return schema

def get_database_schema(force_refresh=False):
    """
    Retrieves the database schema, using a cache by default.
    Schema includes table names (prefixed with 'tab') and their columns with types.

    Args:
        force_refresh (bool): If True, bypass the cache and fetch fresh from DB.

    Returns:
        dict: Database schema. e.g., {"tabSales Invoice": [{"name": "customer", "type": "varchar"}, ...]}
    """
    if not force_refresh:
        cached_schema = frappe.cache().get_value(SCHEMA_CACHE_KEY)
        if cached_schema:
            return cached_schema

    schema = _fetch_schema_from_db()

    if schema: # Only cache if we successfully fetched something
        frappe.cache().set_value(SCHEMA_CACHE_KEY, schema, expires_in_sec=SCHEMA_CACHE_TIMEOUT)

    return schema

def get_formatted_schema_for_llm(force_refresh=False):
    """
    Retrieves and formats the database schema as a string suitable for LLM prompts.
    Example format:
    CREATE TABLE "tabSales Invoice" (
      customer VARCHAR(255),
      posting_date DATE,
      grand_total DECIMAL(18, 6)
    );
    CREATE TABLE "tabCustomer" (
      customer_name VARCHAR(255),
      territory VARCHAR(255)
    );
    """
    schema = get_database_schema(force_refresh=force_refresh)
    if not schema:
        return "Could not retrieve database schema."

    formatted_string = ""
    for table_name, columns in schema.items():
        # SQL-like representation; adjust quoting for specific SQL dialect if necessary.
        # Using double quotes for table and column names for broad compatibility (e.g., PostgreSQL).
        formatted_string += f'CREATE TABLE "{table_name}" (\n'
        col_defs = []
        for col in columns:
            col_defs.append(f'  "{col["name"]}" {col["type"].upper()}')
        formatted_string += ",\n".join(col_defs)
        formatted_string += "\n);\n\n"

    return formatted_string.strip()

# Example of how to make this runnable for testing (if needed)
if __name__ == "__main__":
    # This part would only run if you execute this file directly,
    # and likely needs a Frappe context to be set up to work.
    # For testing within Frappe, use `bench execute` or an API call.
    print("Fetching schema (this might not work outside Frappe context)...")
    # To test, one might need to mock frappe.db and frappe.cache
    # For now, this is just a placeholder.
    # schema_for_llm = get_formatted_schema_for_llm(force_refresh=True)
    # print(schema_for_llm)
    pass
