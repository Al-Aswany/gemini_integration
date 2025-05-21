# Configuration Guide for ERPNext Gemini Integration

This guide provides detailed instructions for configuring and customizing the ERPNext Gemini Integration app after installation.

## Gemini Assistant Settings

The main configuration doctype for the integration. Here you can configure all aspects of the Gemini integration.

### API Configuration

1. Navigate to "Gemini Assistant Settings" in ERPNext
2. In the "API Configuration" section:
   - Enter your Google Gemini API key
   - Select the preferred model:
     - `gemini-pro` for text-only interactions
     - `gemini-pro-vision` for multi-modal interactions
   - Configure temperature (0.0-1.0):
     - Lower values (0.0-0.3): More deterministic responses
     - Medium values (0.4-0.7): Balanced creativity and focus
     - Higher values (0.8-1.0): More creative responses
   - Set maximum tokens for responses
   - Configure retry settings for API calls

### Security Settings

1. In the "Security" section of Gemini Assistant Settings:
   - Enable/disable role-based security
   - Configure sensitive data masking
   - Set up audit logging preferences
   - Configure data retention policies
   - Set up IP restrictions if needed

### Context Awareness

1. In the "Context" section of Gemini Assistant Settings:
   - Enable/disable context awareness
   - Configure history retention (number of messages to retain)
   - Set up document context preferences
   - Configure auto-detection settings
   - Set context switching behavior

### File Processing

1. In the "File Processing" section:
   - Enable/disable file processing
   - Configure allowed file types
   - Set maximum file size limits
   - Configure temporary file storage
   - Set up file processing timeouts

### Workflow Automation

1. In the "Workflow" section:
   - Enable/disable workflow automation
   - Configure default workflow settings
   - Set up AI decision thresholds
   - Configure automation limits
   - Set up notification preferences

## Sensitive Data Configuration

### Adding Sensitive Keywords

1. Navigate to "Gemini Sensitive Keyword" doctype
2. Click "New" to create a new entry
3. Configure the following:
   - Keyword Pattern: Regular expression pattern to match sensitive data
   - Replacement Pattern: What to replace matched data with
   - Is Global: Whether this applies to all doctypes
   - Specific DocTypes: If not global, which doctypes this applies to
   - Specific Fields: If applicable, which fields this applies to
   - Enabled: Whether this pattern is active

### Example Patterns

Here are some example patterns you can use:

#### Credit Card Numbers
- Keyword Pattern: `\b(?:\d{4}[-\s]?){3}\d{4}\b`
- Replacement Pattern: `[CREDIT CARD REDACTED]`

#### Email Addresses
- Keyword Pattern: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
- Replacement Pattern: `[EMAIL REDACTED]`

#### Phone Numbers
- Keyword Pattern: `\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b`
- Replacement Pattern: `[PHONE REDACTED]`

#### Social Security Numbers
- Keyword Pattern: `\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b`
- Replacement Pattern: `[SSN REDACTED]`

## Role Permissions Setup

### Configuring Role Permissions

1. Go to "Role Permission Manager"
2. Search for each Gemini doctype:
   - Gemini Assistant Settings
   - Gemini Conversation
   - Gemini Message
   - Gemini Audit Log
   - Gemini Sensitive Keyword
   - Gemini Feedback
3. For each doctype, configure which roles have:
   - Read permission
   - Write permission
   - Create permission
   - Delete permission
   - Submit permission
   - Cancel permission
   - Amend permission

### Recommended Role Configuration

#### System Manager
- Full access to all Gemini doctypes

#### Administrator
- Full access to all Gemini doctypes

#### Gemini User (Custom Role)
- Read/Write access to Gemini Conversation
- Read/Write access to Gemini Message
- Read access to Gemini Feedback
- No access to Gemini Assistant Settings
- No access to Gemini Audit Log
- No access to Gemini Sensitive Keyword

#### Gemini Administrator (Custom Role)
- Full access to all Gemini doctypes except Audit Log (read-only)

## Workflow Automation Configuration

### Creating Custom Actions

1. Use the ActionHandler class to register custom actions:

```python
from erpnext_gemini_integration.utils.action_handler import ActionHandler

action_handler = ActionHandler()
action_handler.register_action(
    "custom_action_name",
    "Description of the action",
    "module_name",
    "function_name",
    allowed_roles=["System Manager"],
    parameters=["param1", "param2"]
)
```

2. Implement the handler function:

```python
def handle_custom_action(params):
    # Your custom action logic here
    return {"success": True, "message": "Action completed"}
```

### Creating Automation Rules

1. Use the RoleBasedAutomation class to create rules:

```python
from erpnext_gemini_integration.utils.role_based_automation import RoleBasedAutomation

automation = RoleBasedAutomation()
automation.create_rule(
    "rule_name",
    "DocType",
    "event",
    ["Role1", "Role2"],
    [
        {
            "type": "execute_action",
            "action_name": "action_name",
            "params": {
                "param1": "value1",
                "param2": "value2"
            }
        }
    ],
    "Rule description",
    True  # enabled
)
```

### Example: Purchase Order Approval Workflow

```python
from erpnext_gemini_integration.utils.role_based_automation import RoleBasedAutomation

automation = RoleBasedAutomation()
automation.create_rule(
    "po_approval_workflow",
    "Purchase Order",
    "on_submit",
    ["Purchase Manager", "System Manager"],
    [
        {
            "type": "condition",
            "field": "grand_total",
            "operator": "greater_than",
            "value": 10000
        },
        {
            "type": "execute_action",
            "action_name": "send_email",
            "params": {
                "recipients": ["cfo@example.com"],
                "subject": "High-value Purchase Order Submitted: {name}",
                "message": "Purchase Order {name} with amount {grand_total} has been submitted and requires approval."
            }
        },
        {
            "type": "execute_action",
            "action_name": "create_task",
            "params": {
                "subject": "Review Purchase Order {name}",
                "description": "Please review Purchase Order {name} with amount {grand_total}.",
                "assigned_to": "cfo@example.com"
            }
        }
    ],
    "Workflow for high-value purchase order approval",
    True
)
```

## Chat Interface Customization

### Styling the Chat Widget

1. Create a custom CSS file in your site's public folder
2. Override the default styles:

```css
.gemini-chat-widget {
    /* Custom styles */
}

.chat-header {
    /* Custom header styles */
}

.message-content {
    /* Custom message styles */
}
```

3. Include your custom CSS in your site's custom CSS file

### Customizing Chat Behavior

1. Create a custom JS file in your site's public folder
2. Override the default behavior:

```javascript
$(document).on("app_ready", function() {
    // Wait for the original chat to initialize
    setTimeout(function() {
        // Customize behavior
        if (erpnext_gemini_integration && erpnext_gemini_integration.chat) {
            // Override methods as needed
            var originalSendMessage = erpnext_gemini_integration.chat.send_message;
            erpnext_gemini_integration.chat.send_message = function() {
                // Custom logic before sending
                originalSendMessage.apply(this, arguments);
                // Custom logic after sending
            };
        }
    }, 2000);
});
```

## Advanced Configuration

### Custom Prompt Templates

You can customize the prompts used by the Gemini integration:

1. Navigate to the `erpnext_gemini_integration/gemini/prompt_builder.py` file
2. Modify the prompt templates for different contexts
3. Restart your bench after making changes

### Custom Response Parsing

You can customize how responses are parsed:

1. Navigate to the `erpnext_gemini_integration/gemini/response_parser.py` file
2. Modify the parsing logic
3. Restart your bench after making changes

### Custom Context Providers

You can add custom context providers:

1. Create a new Python module in your custom app
2. Implement a context provider function
3. Register it with the context manager

Example:

```python
def custom_context_provider(doctype, docname):
    # Your custom context logic
    return {"custom_data": "value"}

# Register with context manager
from erpnext_gemini_integration.utils.context_manager import ContextManager
context_manager = ContextManager()
# Add your custom provider to the context manager
```

## Performance Tuning

### API Request Optimization

1. In Gemini Assistant Settings:
   - Adjust maximum tokens to balance response quality and API costs
   - Configure caching settings for repeated queries
   - Set appropriate timeout values

### Memory Usage

1. Configure history retention to limit memory usage:
   - Reduce the number of messages kept in conversation history
   - Set up periodic cleanup of old conversations

### Response Time

1. Optimize for faster responses:
   - Use lower temperature settings for more deterministic responses
   - Limit context size for faster processing
   - Configure prompt templates to be concise

## Monitoring and Maintenance

### Audit Logging

1. Review the Gemini Audit Log regularly:
   - Navigate to the "Gemini Audit Log" doctype
   - Filter by date, user, or action type
   - Export logs for compliance purposes

### Usage Analytics

1. Monitor API usage:
   - Track tokens used per conversation
   - Analyze common user queries
   - Identify patterns for optimization

### Regular Maintenance

1. Perform these maintenance tasks regularly:
   - Update the app to the latest version
   - Review and update sensitive data patterns
   - Clean up old conversations and logs
   - Review and adjust role permissions

## Backup and Recovery

### Backing Up Gemini Data

1. Include Gemini doctypes in your regular ERPNext backups
2. Specifically back up these tables:
   - `tabGemini Assistant Settings`
   - `tabGemini Conversation`
   - `tabGemini Message`
   - `tabGemini Audit Log`
   - `tabGemini Sensitive Keyword`
   - `tabGemini Feedback`

### Restoring Gemini Data

1. Restore Gemini data as part of your ERPNext restoration process
2. Verify configuration after restoration
3. Test functionality with a simple query
