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
