# Installation Guide for ERPNext Gemini Integration

This guide provides detailed instructions for installing and configuring the ERPNext Gemini Integration app.

## Prerequisites

Before installing the app, ensure you have:

- ERPNext v14.0.0 or higher
- Python 3.8+
- Valid Google Gemini API key (obtain from [Google AI Studio](https://ai.google.dev/))
- Bench development environment set up
- Administrator access to your ERPNext instance

## Installation Steps

### 1. Install via Bench

```bash
# Navigate to your bench directory
cd ~/frappe-bench

# Get the app from GitHub
bench get-app erpnext_gemini_integration https://github.com/Al-Aswany/gemini_integration

# Install the app on your site
bench --site your-site.com install-app erpnext_gemini_integration

# Update bench
bench update

# Build assets
bench build

# Restart bench
bench restart
```

### 2. Verify Installation

After installation:

1. Log in to your ERPNext instance
2. Navigate to "Installed Apps" in the settings
3. Verify that "ERPNext Gemini Integration" appears in the list

### 3. Initial Configuration

#### Configure API Settings

1. Navigate to "Gemini Assistant Settings" in ERPNext
2. Enter your Google Gemini API key
3. Select the preferred Gemini model:
   - `gemini-pro` for text-only interactions
   - `gemini-pro-vision` for multi-modal (text and image) interactions
4. Configure temperature settings (0.0-1.0):
   - Lower values (0.0-0.3): More deterministic, focused responses
   - Medium values (0.4-0.7): Balanced creativity and focus
   - Higher values (0.8-1.0): More creative, varied responses

#### Security Configuration

1. In "Gemini Assistant Settings", navigate to the "Security" section
2. Enable or disable role-based security
3. Configure sensitive data masking options
4. Set up audit logging preferences

#### Context Awareness Configuration

1. In "Gemini Assistant Settings", navigate to the "Context" section
2. Enable or disable context awareness
3. Configure history retention settings
4. Set up document context preferences

#### File Processing Configuration

1. In "Gemini Assistant Settings", navigate to the "File Processing" section
2. Enable or disable file processing
3. Configure allowed file types
4. Set maximum file size limits

#### Workflow Automation Configuration

1. In "Gemini Assistant Settings", navigate to the "Workflow" section
2. Enable or disable workflow automation
3. Configure default workflow settings

### 4. Role Permissions Setup

Configure which roles can access Gemini features:

1. Go to "Role Permission Manager"
2. Search for the following doctypes:
   - Gemini Assistant Settings
   - Gemini Conversation
   - Gemini Message
   - Gemini Audit Log
   - Gemini Sensitive Keyword
   - Gemini Feedback
3. Configure appropriate permissions for each role

### 5. Sensitive Data Configuration

Set up patterns for masking sensitive information:

1. Navigate to "Gemini Sensitive Keyword" doctype
2. Create new entries for each type of sensitive data:
   - Credit card numbers
   - Social security numbers
   - Email addresses
   - Phone numbers
   - Custom patterns
3. For each entry, specify:
   - Keyword pattern (regex)
   - Replacement pattern
   - Whether it's global or specific to certain doctypes
   - Specific doctypes and fields if applicable

### 6. Testing the Installation

Verify that the installation is working correctly:

1. Click the Gemini chat icon in the ERPNext interface
2. Type a test message like "Hello, are you working correctly?"
3. Verify that you receive a response
4. Test context awareness by navigating to a document and asking about it
5. Test file processing by attaching an image or document

## Troubleshooting

### Common Installation Issues

#### API Key Issues

**Symptom**: Error messages about invalid API key or authentication failures

**Solution**:
- Verify your API key is correctly entered without extra spaces
- Ensure your API key has the necessary permissions
- Check that your Google Cloud billing is set up correctly

#### Module Not Found Errors

**Symptom**: Python errors about missing modules

**Solution**:
- Run `bench pip install -r requirements.txt` from the app directory
- Verify that all dependencies are installed
- Restart bench with `bench restart`

#### Permission Issues

**Symptom**: Users cannot access Gemini features

**Solution**:
- Check role permissions in "Role Permission Manager"
- Verify that users have the necessary roles assigned
- Check for any console errors in the browser

#### Integration Not Appearing

**Symptom**: Gemini chat icon or features don't appear in the interface

**Solution**:
- Run `bench build` to rebuild assets
- Clear browser cache
- Verify the app is installed with `bench list-apps`

### Getting Help

If you encounter issues not covered in this guide:

1. Check the error logs with `bench error-log`
2. Review the Gemini Audit Log doctype for specific errors
3. Contact support at [developer@example.com](mailto:developer@example.com)

## Upgrading

To upgrade the app to a newer version:

```bash
cd ~/frappe-bench
bench update
bench update --pull
bench update --patch
bench build
bench restart
```

## Uninstallation

If you need to uninstall the app:

```bash
cd ~/frappe-bench
bench --site your-site.com uninstall-app erpnext_gemini_integration
bench update
bench build
bench restart
```

Note: Uninstalling will remove all Gemini-related data, including conversations and settings.
