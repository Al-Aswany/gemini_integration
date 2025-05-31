# -*- coding: utf-8 -*-
# Copyright (c) 2025, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import sqlalchemy

from langchain_experimental.sql import SQLDatabaseChain
from langchain.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI # For Gemini

from erpnext_gemini_integration.utils.db_schema import get_database_schema, get_formatted_schema_for_llm

# Safety check imports (will be used more in the next step)
import sqlparse

# --- Database Connection Helper ---
def get_sqlalchemy_engine():
    """
    Creates a SQLAlchemy engine based on Frappe's database configuration.
    """
    db_conf = frappe.conf.db_name
    db_host = frappe.conf.db_host or '127.0.0.1'
    db_port = frappe.conf.db_port or (5432 if frappe.conf.db_type == 'postgres' else 3306)
    db_user = frappe.conf.db_user
    db_password = frappe.conf.db_password
    db_type = frappe.conf.db_type # 'mariadb' or 'postgres'

    if db_type == 'postgres':
        db_uri = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_conf}"
    elif db_type == 'mariadb':
        db_uri = f"mysql+mysqlclient://{db_user}:{db_password}@{db_host}:{db_port}/{db_conf}"
    else:
        raise ValueError("Unsupported database type for LangChain SQL integration.")

    return sqlalchemy.create_engine(db_uri)

# --- LangChain SQL Handler Core ---

# Global variable for the chain - initialize when needed or on first use.
# This is a placeholder; actual initialization might be better within a class or function
# to ensure settings are loaded correctly.
llm = None
db_chain = None
db_schema_cache = None # For the raw schema dict

def initialize_sql_chain(force_refresh_schema=False):
    """
    Initializes the LangChain SQLDatabaseChain with Gemini LLM.
    Caches the DB schema for efficiency.
    """
    global llm, db_chain, db_schema_cache

    if not llm:
        # TODO: Get Gemini API Key from Frappe settings
        # gemini_api_key = frappe.get_doc("Gemini Assistant Settings").get_password("api_key")
        # For now, assuming it might be set in environment for LangChain, or needs explicit passing
        # This part needs to align with how langchain-google-genai expects the API key.
        # It might pick up GOOGLE_API_KEY from os.environ by default.

        # Check if API key is in settings, otherwise LangChain might try OS env
        settings = frappe.get_single("Gemini Assistant Settings")
        gemini_api_key = settings.get_password("api_key")
        if not gemini_api_key:
            frappe.throw(_("Gemini API Key not configured in Gemini Assistant Settings for Langchain use."))

        # Note: The ChatGoogleGenerativeAI might automatically pick up GOOGLE_API_KEY from env.
        # If it needs to be passed explicitly, the constructor might need: google_api_key=gemini_api_key
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=gemini_api_key)
                                     # temperature=0, # Good for SQL generation
                                     # convert_system_message_to_human=True # May be needed for some chains

    if db_chain is None or force_refresh_schema:
        engine = get_sqlalchemy_engine()

        # Fetch the schema as a dictionary first
        current_schema_dict = get_database_schema(force_refresh=force_refresh_schema)
        if not current_schema_dict:
            frappe.throw(_("Failed to retrieve database schema for LangChain initialization."))

        # Get only table names for SQLDatabase include_tables parameter
        include_tables = list(current_schema_dict.keys())

        # Pass the engine and included tables to SQLDatabase
        # SQLDatabase will then perform its own introspection for these tables.
        # Alternatively, a custom prompt with the pre-formatted schema string could be used.
        db = SQLDatabase(engine=engine, include_tables=include_tables)

        # Initialize the SQLDatabaseChain
        # verbose=True can be helpful for debugging
        db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, return_intermediate_steps=True)

        # Cache the raw schema dictionary for other uses if needed (e.g. custom prompts)
        db_schema_cache = current_schema_dict
        frappe.log_error("SQLDatabaseChain initialized/refreshed.", "LangChain SQL Handler")

    return db_chain

def _is_read_only_query(sql_query: str) -> bool:
    """
    Robust check to ensure the query is read-only (SELECT).
    It allows Common Table Expressions (WITH clause) as part of a SELECT.
    """
    if not sql_query or not sql_query.strip():
        return False # Empty query is not a valid SELECT

    try:
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            # Could not parse, treat as unsafe
            frappe.log_error(f"SQL safety check: Could not parse query: {sql_query}", "LangChain SQL Safety")
            return False

        for stmt in parsed:
            # The main statement type must be SELECT.
            # A query starting with WITH is also SELECT-like in its ultimate effect.
            if stmt.get_type() not in ('SELECT', 'WITH'):
                frappe.log_error(f"SQL safety check: Non-SELECT/WITH statement type '{stmt.get_type()}' found: {sql_query}", "LangChain SQL Safety")
                return False

            # Additionally, iterate through tokens to look for forbidden keywords
            # outside of comments or strings, just in case the parser misses something
            # or to be extra cautious. This is a deeper check.
            disallowed_keywords = [
                'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE',
                'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'SAVEPOINT',
                'EXECUTE', 'CALL' # EXECUTE and CALL might be used by some DBs for stored procs
            ]

            # Flatten all tokens for easier checking, ignoring whitespace and comments
            tokens = [t for t in stmt.flatten() if not t.is_whitespace and not isinstance(t.ttype, sqlparse.tokens.Comment)]

            for token in tokens:
                if token.ttype in (sqlparse.tokens.Keyword, sqlparse.tokens.Keyword.DML, sqlparse.tokens.Keyword.DDL) and                    token.value.upper() in disallowed_keywords:
                    # Check if it's the main SELECT keyword of a CTE, which is fine
                    if token.value.upper() == 'SELECT' and stmt.get_type() == 'WITH':
                        # This is a SELECT inside a CTE, which is part of a larger SELECT-like structure
                        continue

                    frappe.log_error(f"SQL safety check: Disallowed keyword '{token.value.upper()}' found: {sql_query}", "LangChain SQL Safety")
                    return False

        # If all statements are SELECT or WITH and no disallowed keywords are found at critical places
        return True

    except Exception as e:
        frappe.log_error(f"SQL safety check: Error during parsing: {str(e)} for query: {sql_query}", "LangChain SQL Safety")
        return False # Fail safe

def _log_generated_sql(natural_query, sql_query, status="Success", error_message=None):
    """Logs the generated SQL query to the audit log."""
    try:
        frappe.get_doc({
            "doctype": "Gemini Audit Log", # Assuming this doctype is suitable
            "timestamp": frappe.utils.now_datetime(),
            "user": frappe.session.user,
            "action_type": "Text-to-SQL",
            "details": frappe.as_json({
                "natural_language_query": natural_query,
                "generated_sql": sql_query,
                "status": status,
                "error_message": error_message if error_message else ""
            }),
            "status": status, # "Success" or "Error"
            "ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "127.0.0.1"
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to log generated SQL: {str(e)}", "LangChain SQL Audit")


def text_to_sql_with_results(natural_language_query: str):
    """
    Takes a natural language query, converts it to SQL using LangChain,
    executes it safely, and returns the results.
    """
    try:
        chain = initialize_sql_chain()

        # Get the SQL query from LangChain
        # The result from SQLDatabaseChain can be a dict with 'query' and 'result'
        # or directly the SQL string depending on how it's configured or used.
        # For SQLDatabaseChain, invoking it with the query directly should give SQL.
        # If it executes directly, we need to manage that.
        # Let's assume we want to get the SQL first.

        # The chain.run(query) or chain.invoke({"query": natural_language_query})
        # often directly returns the final answer after executing the SQL.
        # To get the SQL, we might need to inspect intermediate steps or customize the chain.

        # If SQLDatabaseChain directly executes and returns final answer:
        # response = chain.invoke({"query": natural_language_query})
        # generated_sql = response.get("intermediate_steps", [{}])[0].get("sql_cmd", "Unavailable") # Example path
        # results_str = response.get("result", "")

        # Let's try to get SQL first using `return_sql=True` if available, or parse from intermediate steps
        # Based on documentation, SQLDatabaseChain's `run` method can take `callbacks`
        # or `return_intermediate_steps=True` in constructor helps.

        chain_input = {"query": natural_language_query}
        chain_result = chain(chain_input) # Use __call__ or invoke based on LangChain version

        generated_sql = ""
        intermediate_steps = chain_result.get("intermediate_steps", [])
        if intermediate_steps and isinstance(intermediate_steps, list) and len(intermediate_steps) > 0:
            # The structure of intermediate_steps can vary.
            # Typically for SQLDatabaseChain, it's a list of dictionaries.
            # The SQL query is often in a dictionary within this list.
            # We need to find the actual SQL command.
            for step in intermediate_steps:
                if isinstance(step, dict) and "sql_cmd" in step: # Older versions
                     generated_sql = step["sql_cmd"]
                     break
                # For newer versions, intermediate steps might be structured differently
                # e.g. a list containing tuples or other objects.
                # This part might need refinement after testing with the specific LangChain version.
                # For now, let's assume a common pattern.
                # A more robust way is to parse the string representation of intermediate_steps if it's complex.
                # Or, use a custom chain for more control.

                # Fallback: Try to find something that looks like SQL
                if isinstance(step, str) and ("SELECT" in step.upper() or "WITH" in step.upper()):
                    generated_sql = step
                    break
                elif isinstance(step, dict): # Check dict values
                    for val in step.values():
                         if isinstance(val, str) and ("SELECT" in val.upper() or "WITH" in val.upper()):
                              generated_sql = val
                              break
                    if generated_sql: break


        if not generated_sql:
            # If we couldn't extract SQL from intermediate_steps, it might be that the LLM failed
            # or the chain structure is different. The 'result' might contain an error or direct answer.
            # This indicates an issue with SQL generation or extraction.
            _log_generated_sql(natural_language_query, "No SQL Generated", "Error", chain_result.get("result"))
            return {"error": "Could not generate SQL query from the question.", "details": chain_result.get("result")}

        # Clean up the SQL - remove potential ```sql ... ``` markers if LLM adds them
        if generated_sql.strip().startswith("```sql"):
            generated_sql = generated_sql.strip()[5:]
            if generated_sql.strip().endswith("```"):
                generated_sql = generated_sql.strip()[:-3]
        generated_sql = generated_sql.strip()


        # Safety Check
        if not _is_read_only_query(generated_sql):
            _log_generated_sql(natural_language_query, generated_sql, "Error", "Attempted non-SELECT query.")
            raise PermissionError("Generated query is not read-only (SELECT). Execution denied.")

        # Execute the SQL (LangChain's SQLDatabaseChain usually executes it, result is in 'result')
        # The 'result' key from chain_result should contain the database output as a string.
        db_results_str = chain_result.get("result")

        # Log the SQL
        _log_generated_sql(natural_language_query, generated_sql, "Success")

        # The result from SQLDatabaseChain is often a string representation of the SQL output.
        # It needs to be parsed if we want a structured format (e.g., list of dicts).
        # For now, we return the string result. If direct execution via frappe.db.sql is preferred
        # for structured output, the chain needs to be configured to only return SQL.
        # If `db_results_str` is indeed the direct result, we try to parse it.
        # However, `frappe.db.sql` is better for getting structured results.

        # Re-executing with frappe.db.sql to get structured data
        # This is safer and gives us control over the output format.
        try:
            # Limit results for safety and pagination preview
            # This is a simple limit; true pagination needs more complex SQL modification
            # or different chain handling.
            # For now, let's just add a LIMIT clause if not present.
            # This is a basic heuristic and might break complex queries (e.g. with existing LIMIT or subqueries)

            # A better way for pagination is to parse the result from the chain if it's a list of tuples/dicts
            # or modify the chain to support limits.
            # For now, let's execute with frappe.db.sql to get structured data.

            # Max rows to fetch initially
            MAX_ROWS_DEFAULT = 100

            # We need to be careful about modifying SQL generated by LLM.
            # Adding LIMIT might be okay for simple SELECTs.
            # A more robust solution would be to have the LLM generate SQL with LIMIT based on prompt,
            # or handle this in the result processing if the chain returns all results.

            # For now, let's execute the SQL as is and handle large results by truncating the list.
            results_list = frappe.db.sql(generated_sql, as_dict=True)

            has_more_results = False
            if len(results_list) > MAX_ROWS_DEFAULT:
                results_list = results_list[:MAX_ROWS_DEFAULT]
                has_more_results = True

        except Exception as e:
            _log_generated_sql(natural_language_query, generated_sql, "Error", f"SQL Execution Error: {str(e)}")
            return {"error": f"Error executing SQL query: {str(e)}", "generated_sql": generated_sql}

        return {
            "natural_query": natural_language_query,
            "generated_sql": generated_sql,
            "results": results_list,
            "has_more_results": has_more_results,
            "message": f"Successfully executed query. {'Showing first ' + str(MAX_ROWS_DEFAULT) + ' results.' if has_more_results else ''}"
        }

    except PermissionError as pe: # Catch our specific safety error
        frappe.log_error(f"Langchain SQL Error: {str(pe)} for query: {natural_language_query}", "LangChain SQL Safety")
        return {"error": str(pe)}
    except Exception as e:
        frappe.log_error(f"Langchain SQL Error: {str(e)} for query: {natural_language_query}", "LangChain SQL Handler")
        # Attempt to initialize chain again if it's a general error, could be transient
        initialize_sql_chain(force_refresh_schema=True) # Force schema refresh on error
        return {"error": f"An error occurred: {str(e)}"}

# Ensure __init__.py exists in gemini directory
