# ERPNext Gemini Integration App

A comprehensive integration between ERPNext and Google's Gemini AI, providing intelligent automation, context-aware assistance, and workflow optimization.

## Features

- **AI-Powered Chat Interface**: Interact with Gemini AI directly within ERPNext
- **Context Awareness**: AI understands your current document context
- **Multi-Modal Processing**: Process text, images, and documents
- **Workflow Automation**: Automate business processes with AI assistance
- **Role-Based Security**: Enterprise-grade security and permissions
- **Audit Logging**: Comprehensive tracking of all AI interactions

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

## Examples

### Example 1: Sales Order Analysis

```
User: Analyze this Sales Order and suggest next steps.
Gemini: Based on this Sales Order (#SO-00123):
- Customer has ordered 10 units of Product A ($5,000 total)
- Delivery is scheduled for next week
- This is a repeat customer with good payment history

Suggested next steps:
1. Confirm inventory availability for Product A
2. Schedule production if needed
3. Contact shipping department for delivery planning
4. Prepare invoice documentation
```

### Example 2: Purchase Order Workflow

```
User: Create a workflow for Purchase Order approval.
Gemini: I've created a workflow for Purchase Order approval:

1. When a new Purchase Order is submitted:
   - Notify the Purchasing Manager
   - Create an approval task

2. When approved:
   - Automatically send to vendor
   - Create follow-up reminder for 3 days

3. When items are received:
   - Trigger quality check
   - Update inventory

Would you like me to implement this workflow?
```

## Troubleshooting

### Common Issues

1. **API Key Issues**:
   - Ensure your Gemini API key is valid and correctly entered
   - Check API usage limits and billing status

2. **Permission Errors**:
   - Verify user has proper role permissions
   - Check role-based security settings

3. **Context Awareness Not Working**:
   - Ensure context awareness is enabled in settings
   - Verify the doctype is supported for context

### Logs

Check the following logs for troubleshooting:

- Frappe error logs: `bench error-log`
- Gemini Audit Log doctype for detailed interaction history
- Browser console for frontend issues

## Development and Customization

### Directory Structure

```
erpnext_gemini_integration/
├── erpnext_gemini_integration/
│   ├── gemini/              # Core Gemini API integration
│   ├── api/                 # API endpoints
│   ├── utils/               # Utility functions
│   ├── public/              # Frontend assets
│   │   ├── js/
│   │   └── css/
│   ├── templates/           # HTML templates
│   └── modules/             # Module definitions
├── setup.py                 # Package setup
└── requirements.txt         # Dependencies
```

### Adding Custom Actions

Create custom action handlers:

1. Add a new function in `action_handlers.py`
2. Register the action using the ActionHandler class
3. Configure permissions and parameters

Example:

```python
def handle_custom_action(params):
    # Your custom action logic here
    return {"success": True, "message": "Custom action completed"}

# Register the action
from erpnext_gemini_integration.utils.action_handler import ActionHandler
action_handler = ActionHandler()
action_handler.register_action(
    "custom_action",
    "Description of custom action",
    "erpnext_gemini_integration.utils.action_handlers",
    "handle_custom_action",
    allowed_roles=["System Manager"],
    parameters=["param1", "param2"]
)
```

## License

This application is licensed under the MIT License.

## Support

For support, please contact the developer at [developer@example.com](mailto:developer@example.com).
