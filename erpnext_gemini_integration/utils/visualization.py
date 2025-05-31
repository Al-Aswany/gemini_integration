# -*- coding: utf-8 -*-
# Copyright (c) 2025, Your Name and contributors
# For license information, please see license.txt

import frappe
import matplotlib
matplotlib.use('Agg') # Use a non-interactive backend suitable for web servers
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import pandas as pd

def _generate_bar_chart(df, title="Bar Chart"):
    """Generates a bar chart from a Pandas DataFrame."""
    if df.empty or len(df.columns) < 2:
        return None # Not enough data

    try:
        # Assume first column is x-axis (categories), second is y-axis (values)
        # This is a heuristic and might need to be smarter based on data types / LLM hints
        x_col = df.columns[0]
        y_col = df.columns[1]

        # Ensure y_col is numeric
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            # Attempt conversion if possible, or return None
            try:
                df[y_col] = pd.to_numeric(df[y_col])
            except ValueError:
                return None


        plt.figure(figsize=(10, 6))
        df.plot(kind='bar', x=x_col, y=y_col, legend=False)
        plt.title(title)
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        plt.close() # Close the figure to free memory

        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        frappe.log_error(f"Failed to generate bar chart: {str(e)}")
        return None

def _generate_line_chart(df, title="Line Chart"):
    """Generates a line chart from a Pandas DataFrame."""
    if df.empty or len(df.columns) < 2:
        return None

    try:
        x_col = df.columns[0]
        y_col = df.columns[1]

        if not pd.api.types.is_numeric_dtype(df[y_col]):
            try:
                df[y_col] = pd.to_numeric(df[y_col])
            except ValueError:
                 return None

        # If x_col looks like dates, try to convert for better plotting
        if pd.api.types.is_string_dtype(df[x_col]) or pd.api.types.is_object_dtype(df[x_col]):
            try:
                df[x_col] = pd.to_datetime(df[x_col])
            except (ValueError, TypeError):
                pass # Keep as is if conversion fails

        plt.figure(figsize=(10, 6))
        df.plot(kind='line', x=x_col, y=y_col, legend=False)
        plt.title(title)
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        plt.close()

        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        frappe.log_error(f"Failed to generate line chart: {str(e)}")
        return None

def _generate_pie_chart(df, title="Pie Chart"):
    """Generates a pie chart from a Pandas DataFrame."""
    if df.empty or len(df.columns) < 2:
        return None
    if len(df) > 10 : # Pie charts are not good for too many categories
        return {"type": "message", "content": "Pie chart is not suitable for this data (too many categories). Try a bar chart."}

    try:
        labels_col = df.columns[0]
        values_col = df.columns[1]

        if not pd.api.types.is_numeric_dtype(df[values_col]):
            try:
                df[values_col] = pd.to_numeric(df[values_col])
            except ValueError:
                return None

        plt.figure(figsize=(8, 8))
        df.plot(kind='pie', y=values_col, labels=df[labels_col], autopct='%1.1f%%', startangle=90, legend=False)
        plt.title(title)
        plt.ylabel('') # Hide y-label for pie charts
        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        plt.close()

        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        frappe.log_error(f"Failed to generate pie chart: {str(e)}")
        return None

def _generate_html_table(df):
    """Generates an HTML table from a Pandas DataFrame."""
    if df.empty:
        return "<p>No data to display.</p>"
    try:
        return df.to_html(classes=["table", "table-striped", "table-bordered"], border=0, index=False)
    except Exception as e:
        frappe.log_error(f"Failed to generate HTML table: {str(e)}")
        return "<p>Error generating table view.</p>"

def infer_chart_type_and_title(data: list[dict], natural_query: str, generated_sql: str):
    """
    Infers the most appropriate chart type based on data and query.
    This is a basic heuristic and can be improved with LLM assistance or more rules.
    Returns (chart_type, chart_title)
    chart_type can be 'bar', 'line', 'pie', 'table'
    """
    if not data:
        return 'table', "Query Results" # Default to table if no data

    df = pd.DataFrame(data)
    num_rows, num_cols = df.shape

    # Simple title from natural query
    chart_title = f"Visualization for: {natural_query[:50]}{'...' if len(natural_query) > 50 else ''}"

    if num_cols == 0:
        return 'table', chart_title

    # Heuristics based on column count and types
    if num_cols == 2:
        col1_type = df.dtypes[df.columns[0]]
        col2_type = df.dtypes[df.columns[1]]

        is_col1_numeric = pd.api.types.is_numeric_dtype(col1_type)
        is_col1_datetime = pd.api.types.is_datetime64_any_dtype(col1_type)
        is_col1_categorical = pd.api.types.is_string_dtype(col1_type) or pd.api.types.is_object_dtype(col1_type)

        is_col2_numeric = pd.api.types.is_numeric_dtype(col2_type)
        # is_col2_datetime = pd.api.types.is_datetime64_any_dtype(col2_type)
        # is_col2_categorical = pd.api.types.is_string_dtype(col2_type) or pd.api.types.is_object_dtype(col2_type)

        if (is_col1_categorical or is_col1_datetime) and is_col2_numeric:
            if "month" in natural_query.lower() or "date" in natural_query.lower() or "time" in natural_query.lower() or is_col1_datetime:
                if num_rows > 1: # Line charts need multiple points
                     return 'line', chart_title
            if num_rows <= 15 : # Bar chart for reasonable number of categories
                return 'bar', chart_title

        if is_col1_categorical and is_col2_numeric and num_rows <= 10: # Pie for few categories
            return 'pie', chart_title

    # Default to table for other cases or if specific chart conditions aren't met
    return 'table', chart_title


def generate_visualization(data: list[dict], natural_query: str, generated_sql: str, requested_chart_type: str = None):
    """
    Generates a data visualization (chart or table) from SQL query results.

    Args:
        data (list[dict]): Data from the SQL query.
        natural_query (str): The original natural language query.
        generated_sql (str): The SQL query that produced the data.
        requested_chart_type (str, optional): 'bar', 'line', 'pie', 'table'. Defaults to None (infer).

    Returns:
        dict: {"type": "image_uri" | "html_table" | "message", "content": data_uri_string | html_string | error_message_string, "chart_title": "..."}
    """
    if not data:
        return {"type": "message", "content": "No data returned from the query to visualize.", "chart_title": "Empty Result"}

    df = pd.DataFrame(data)

    # Handle user's visualization request sanity
    # This is a very basic check. More sophisticated checks could involve LLM reasoning.
    if requested_chart_type == 'pie' and (len(df.columns) < 2 or len(df) > 10):
        return {"type": "message", "content": "A pie chart is not suitable for this data (requires 2 columns and few categories). I can provide a table.", "chart_title": "Visualization Request"}
    if requested_chart_type in ['line', 'bar'] and len(df.columns) < 2:
         return {"type": "message", "content": f"A {requested_chart_type} chart requires at least 2 columns of data. I can provide a table.", "chart_title": "Visualization Request"}


    chart_type_to_generate, chart_title = infer_chart_type_and_title(data, natural_query, generated_sql)

    if requested_chart_type and requested_chart_type in ['bar', 'line', 'pie', 'table']:
        chart_type_to_generate = requested_chart_type
        # Potentially update title if user requested specific chart
        chart_title = f"{requested_chart_type.capitalize()} Chart for: {natural_query[:50]}{'...' if len(natural_query) > 50 else ''}"


    visualization_content = None
    vis_type = "message" # Default to message if no chart generated

    if chart_type_to_generate == 'bar':
        visualization_content = _generate_bar_chart(df.copy(), title=chart_title)
        if visualization_content: vis_type = "image_uri"
    elif chart_type_to_generate == 'line':
        visualization_content = _generate_line_chart(df.copy(), title=chart_title)
        if visualization_content: vis_type = "image_uri"
    elif chart_type_to_generate == 'pie':
        # _generate_pie_chart might return a dict if it thinks it's unsuitable
        pie_result = _generate_pie_chart(df.copy(), title=chart_title)
        if isinstance(pie_result, str): # It's a base64 string
            visualization_content = pie_result
            vis_type = "image_uri"
        elif isinstance(pie_result, dict): # It's a message like {"type": "message", "content": ...}
            return {**pie_result, "chart_title": chart_title} # Return the message directly
        # else: None, will fall through

    # Fallback to table if no specific chart was generated or if table was chosen
    if not visualization_content or chart_type_to_generate == 'table':
        visualization_content = _generate_html_table(df.copy())
        vis_type = "html_table"
        chart_title = f"Table View: {natural_query[:50]}{'...' if len(natural_query) > 50 else ''}"


    if not visualization_content:
        return {"type": "message", "content": "Sorry, I could not generate a visualization for this data.", "chart_title": chart_title}

    return {"type": vis_type, "content": visualization_content, "chart_title": chart_title}
