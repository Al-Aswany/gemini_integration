# ERPNext Gemini Integration

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Al-Aswany/gemini_integration)

A comprehensive integration between ERPNext and Google's Gemini AI, providing intelligent automation, context-aware assistance, and workflow optimization.

## Features

- **AI-Powered Chat Interface**: Interact with Gemini AI directly within ERPNext
- **Context Awareness**: AI understands your current document context
- **Multi-Modal Processing**: Process text, images, and documents
- **Workflow Automation**: Automate business processes with AI assistance
- **Role-Based Security**: Enterprise-grade security and permissions
- **Audit Logging**: Comprehensive tracking of all AI interactions

## Text-to-SQL and Data Visualization

This integration now includes powerful Text-to-SQL capabilities and data visualization within the chat interface, powered by LangChain and Google Gemini.

### Asking Database Questions

To ask a question that should be translated into a database query, prefix your message with `QueryDB: `.

For example:
`QueryDB: Show me the total sales amount for each customer this year.`
`QueryDB: List items with stock below 50.`

The chatbot will:
1. Translate your natural language question into an SQL query.
2. Execute the SQL query safely against the ERPNext database (read-only `SELECT` statements only).
3. Return the query results in a structured format (JSON/dict).
4. Log the generated SQL query for auditing purposes.

### Data Visualization

When you ask a database query using the `QueryDB:` prefix, the system will also attempt to generate a visualization of the results:

- **Tables**: For general query results or when other chart types are not suitable, a table view of the data is provided.
- **Bar Charts**: Typically generated for categorical data comparisons (e.g., sales per customer).
- **Line Charts**: Often used for time-series data (e.g., sales over months).
- **Pie Charts**: Used for proportional data with a small number of categories.

The visualization will be embedded directly into the chat response. If a specific chart type doesn't make sense for the data (e.g., asking for a pie chart of textual descriptions), the chatbot will inform you.

**Example Interaction:**

**User:** `QueryDB: What were the monthly sales totals for the last 3 months?`

**Chatbot:**
*   **Generated SQL:** `SELECT strftime('%Y-%m', posting_date) as sales_month, SUM(grand_total) as total_sales FROM \`tabSales Invoice\` WHERE posting_date >= date('now', '-3 months') GROUP BY sales_month ORDER BY sales_month;`
*   **Results:** `[{"sales_month": "2024-05", "total_sales": 12000.00}, ...]`
*   **Visualization:** (An embedded bar chart showing total sales for each of the last 3 months)

### Large Result Sets

If a query returns a large number of rows (e.g., more than 100), the chatbot will display the first 100 rows and indicate that more results are available. You may need to refine your query to get a more specific dataset.

## App Structure

This app follows the standard Frappe app structure:

```
erpnext_gemini_integration/
├── docs/                           # Documentation files
├── erpnext_gemini_integration/     # Main app directory
│   ├── api/                        # API endpoints
│   ├── config/                     # App configuration
│   │   ├── desktop.py              # Desktop configuration
│   │   └── docs.py                 # Documentation configuration
│   ├── erpnext_gemini_integration/ # Module directory
│   │   ├── doctype/                # DocTypes directory
│   │   │   ├── gemini_assistant_settings/
│   │   │   ├── gemini_conversation/
│   │   │   ├── gemini_message/
│   │   │   ├── gemini_audit_log/
│   │   │   ├── gemini_sensitive_keyword/
│   │   │   └── gemini_feedback/
│   ├── gemini/                     # Gemini API integration
│   ├── public/                     # Static assets
│   │   ├── css/
│   │   └── js/
│   ├── templates/                  # HTML templates
│   ├── utils/                      # Utility functions
│   ├── hooks.py                    # Frappe hooks
│   ├── modules.txt                 # Module definition
│   └── patches.txt                 # Database patches
├── requirements.txt                # Python dependencies
└── setup.py                        # Package setup
```

## Installation

### Prerequisites

- ERPNext v14.0.0 or higher
- Python 3.8+
- Valid Google Gemini API key

### Installation Steps

1. Install the app using bench:

```bash
cd ~/frappe-bench
bench get-app erpnext_gemini_integration https://github.com/Al-Aswany/gemini_integration
bench install-app erpnext_gemini_integration
```

2. After installation, restart your bench:

```bash
bench restart
```

3. Configure the Gemini API key:
   - Navigate to "Gemini Assistant Settings" in ERPNext
   - Enter your Google Gemini API key
   - Configure other settings as needed

### Added Dependencies for Advanced Features (Text-to-SQL and Visualization)

The following Python libraries have been added to support Text-to-SQL and data visualization features. They are included in `requirements.txt` and will be installed with the app or when `pip install -r requirements.txt` is run:

- `langchain`: Core LangChain library.
- `langchain-experimental`: For experimental LangChain features, including SQLDatabaseChain.
- `SQLAlchemy`: Used by LangChain for database interaction.
- `psycopg2-binary`: PostgreSQL driver (adapt if your ERPNext uses MariaDB/MySQL, e.g., `mysqlclient`).
- `matplotlib`: For generating charts.
- `plotly`: For generating interactive charts (alternative/complementary to matplotlib).
- `langchain-google-genai`: Provides LangChain integration with Google's Gemini models.

Ensure your bench environment can install these packages (e.g., system dependencies for `psycopg2-binary` or `matplotlib` might be needed).

## Configuration

### Gemini Assistant Settings

The main configuration doctype for the integration. Here you can set:

- **API Configuration**: API key, model selection, temperature settings
- **Security Settings**: Enable/disable role-based security, sensitive data masking
- **Context Settings**: Enable/disable context awareness, history retention
- **File Processing**: Enable/disable file processing, allowed file types
- **Workflow Settings**: Enable/disable workflow automation

### Sensitive Keywords

Configure patterns for masking sensitive information:

1. Navigate to "Gemini Sensitive Keyword" doctype
2. Add patterns for sensitive data (credit cards, emails, etc.)
3. Specify replacement patterns and scope (global or specific doctypes)

### Role Permissions

Set up role-based access to Gemini features:

1. Go to "Role Permission Manager"
2. Configure permissions for Gemini doctypes based on user roles
3. Ensure proper security for sensitive operations

## Usage

### Chat Interface

The chat widget provides direct access to Gemini AI:

1. Click the Gemini icon in the ERPNext interface
2. Type your question or request
3. Gemini will respond with context-aware answers
4. Attach files for multi-modal processing

### Context Awareness

The app automatically detects your current context:

- When viewing a document, Gemini understands the doctype and fields
- Conversations maintain history for continuous interaction
- Document-specific insights are provided based on context

### File Processing

Process various file types for analysis:

- Images: JPG, PNG, GIF, WebP
- Documents: PDF, TXT, CSV, JSON, XLSX, DOCX
- Code: PY, JS, HTML, CSS, JSON, XML

### Workflow Automation

Automate business processes with AI assistance:

1. Navigate to "Workflow Automation" section
2. Create rules based on document events
3. Configure actions and conditions
4. Set up role-based permissions for automation

## Documentation

For detailed documentation, please refer to the docs folder:

- [Installation Guide](docs/installation_guide.md)
- [Configuration Guide](docs/configuration_guide.md)
- [Test Cases](docs/test_cases.md)

## License

This application is licensed under the MIT License.

## Support

For support, please contact the developer at [developer@example.com](mailto:developer@example.com)
