# Test Cases for ERPNext Gemini Integration

This document outlines comprehensive test cases for the ERPNext Gemini Integration app to ensure all features work correctly and securely.

## API Integration Tests

### API Key Configuration

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| API-001 | Valid API key configuration | 1. Navigate to Gemini Assistant Settings<br>2. Enter valid API key<br>3. Save settings | Settings saved successfully |
| API-002 | Invalid API key handling | 1. Navigate to Gemini Assistant Settings<br>2. Enter invalid API key<br>3. Save settings<br>4. Test chat functionality | Error message displayed when attempting to use chat |
| API-003 | Empty API key handling | 1. Navigate to Gemini Assistant Settings<br>2. Clear API key<br>3. Save settings<br>4. Test chat functionality | Error message indicating API key is required |

### API Request/Response

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| API-004 | Basic text generation | 1. Configure valid API key<br>2. Send simple text prompt<br>3. Verify response | Coherent response received from API |
| API-005 | Rate limiting handling | 1. Configure valid API key<br>2. Send multiple requests in quick succession | Proper rate limit handling with exponential backoff |
| API-006 | Error handling | 1. Configure valid API key<br>2. Force an API error (e.g., by sending malformed request) | Graceful error handling with user-friendly message |
| API-007 | Timeout handling | 1. Configure valid API key<br>2. Set very low timeout value<br>3. Send complex prompt | Proper timeout handling with user notification |

## Chat Interface Tests

### Basic Functionality

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| CHAT-001 | Chat widget visibility | 1. Log in as user with chat permissions<br>2. Verify chat icon is visible | Chat icon visible in interface |
| CHAT-002 | Chat widget opening | 1. Click chat icon<br>2. Verify chat widget opens | Chat widget opens correctly |
| CHAT-003 | Sending message | 1. Open chat widget<br>2. Type message<br>3. Send message | Message appears in chat and response received |
| CHAT-004 | Message history | 1. Send multiple messages<br>2. Close chat widget<br>3. Reopen chat widget | Previous messages are displayed |

### Responsive Design

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| CHAT-005 | Desktop layout | 1. Open chat widget on desktop<br>2. Verify layout | Widget displays correctly on desktop |
| CHAT-006 | Mobile layout | 1. Open chat widget on mobile or emulated mobile device<br>2. Verify layout | Widget adapts to mobile screen size |
| CHAT-007 | Tablet layout | 1. Open chat widget on tablet or emulated tablet device<br>2. Verify layout | Widget adapts to tablet screen size |

## Context Awareness Tests

### Document Context

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| CTX-001 | Form view context | 1. Open a document (e.g., Sales Order)<br>2. Open chat widget<br>3. Ask about current document | Response includes information about current document |
| CTX-002 | List view context | 1. Open a list view (e.g., Sales Orders)<br>2. Open chat widget<br>3. Ask about current list | Response acknowledges current list context |
| CTX-003 | Dashboard context | 1. Open a dashboard<br>2. Open chat widget<br>3. Ask about dashboard data | Response acknowledges dashboard context |

### Context Switching

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| CTX-004 | Automatic context switching | 1. Open document A<br>2. Start chat<br>3. Navigate to document B<br>4. Continue chat | Context switches to document B |
| CTX-005 | Context retention | 1. Open document<br>2. Start conversation about document<br>3. Ask follow-up question without document reference | Follow-up response maintains document context |

## File Processing Tests

### Image Processing

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| FILE-001 | JPG image upload | 1. Open chat widget<br>2. Upload JPG image<br>3. Ask about image | Response includes analysis of image |
| FILE-002 | PNG image upload | 1. Open chat widget<br>2. Upload PNG image<br>3. Ask about image | Response includes analysis of image |
| FILE-003 | Large image handling | 1. Open chat widget<br>2. Upload large image (>5MB)<br>3. Ask about image | Image is properly compressed or error message displayed |

### Document Processing

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| FILE-004 | PDF document upload | 1. Open chat widget<br>2. Upload PDF document<br>3. Ask about document content | Response includes analysis of document content |
| FILE-005 | CSV data upload | 1. Open chat widget<br>2. Upload CSV file<br>3. Ask for data analysis | Response includes analysis of CSV data |
| FILE-006 | XLSX data upload | 1. Open chat widget<br>2. Upload XLSX file<br>3. Ask for data analysis | Response includes analysis of Excel data |

## Workflow Automation Tests

### Document Event Hooks

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| FLOW-001 | Document creation hook | 1. Configure automation for document creation<br>2. Create new document | Automation triggered successfully |
| FLOW-002 | Document update hook | 1. Configure automation for document update<br>2. Update existing document | Automation triggered successfully |
| FLOW-003 | Document submission hook | 1. Configure automation for document submission<br>2. Submit document | Automation triggered successfully |

### Custom Actions

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| FLOW-004 | Email notification action | 1. Configure email notification action<br>2. Trigger action via workflow | Email sent successfully |
| FLOW-005 | Task creation action | 1. Configure task creation action<br>2. Trigger action via workflow | Task created successfully |
| FLOW-006 | Document update action | 1. Configure document update action<br>2. Trigger action via workflow | Document updated successfully |

### Role-Based Automation

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| FLOW-007 | Role-based rule execution | 1. Configure rule for specific role<br>2. Trigger event as user with role<br>3. Trigger event as user without role | Rule executes only for user with role |
| FLOW-008 | Multiple role rule | 1. Configure rule for multiple roles<br>2. Trigger event as users with different roles | Rule executes for all specified roles |

### AI-Driven Decision Making

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| FLOW-009 | Classification decision | 1. Configure AI classification decision<br>2. Trigger workflow with test data | Correct classification made |
| FLOW-010 | Extraction decision | 1. Configure AI extraction decision<br>2. Trigger workflow with test data | Correct data extracted |
| FLOW-011 | Decision with conditions | 1. Configure AI decision with conditions<br>2. Trigger workflow with test data | Decision and conditions properly evaluated |

## Security Tests

### Sensitive Data Handling

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| SEC-001 | Credit card masking | 1. Configure credit card pattern<br>2. Send message containing credit card number | Credit card number is masked in logs and responses |
| SEC-002 | Email masking | 1. Configure email pattern<br>2. Send message containing email | Email is masked in logs and responses |
| SEC-003 | Custom pattern masking | 1. Configure custom sensitive pattern<br>2. Send message containing pattern | Pattern is masked in logs and responses |

### Role-Based Access

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| SEC-004 | Admin access | 1. Log in as Administrator<br>2. Verify access to all Gemini doctypes | Full access to all doctypes |
| SEC-005 | Limited user access | 1. Create user with limited role<br>2. Verify access to Gemini doctypes | Access only to permitted doctypes |
| SEC-006 | No permission user | 1. Create user with no Gemini permissions<br>2. Verify access to Gemini features | No access to Gemini features |

### Audit Logging

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| SEC-007 | Chat interaction logging | 1. Send message in chat<br>2. Check Gemini Audit Log | Interaction logged with user, timestamp, and content |
| SEC-008 | Workflow execution logging | 1. Trigger workflow automation<br>2. Check Gemini Audit Log | Workflow execution logged with details |
| SEC-009 | API request logging | 1. Make API request<br>2. Check Gemini Audit Log | API request logged with details |

## Performance Tests

### Response Time

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| PERF-001 | Simple query response time | 1. Send simple query<br>2. Measure response time | Response received within acceptable time (<3s) |
| PERF-002 | Complex query response time | 1. Send complex query<br>2. Measure response time | Response received within acceptable time (<10s) |
| PERF-003 | Image analysis response time | 1. Send image for analysis<br>2. Measure response time | Response received within acceptable time (<15s) |

### Concurrent Users

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| PERF-004 | Multiple concurrent chats | 1. Open multiple browser sessions<br>2. Start chat in each session<br>3. Send messages concurrently | All chats function correctly without interference |
| PERF-005 | System load under concurrent use | 1. Simulate multiple users using the system<br>2. Monitor system resources | System remains responsive with acceptable resource usage |

## Edge Cases and Error Handling

### Network Issues

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| ERR-001 | Network interruption | 1. Start chat<br>2. Disconnect network during API call<br>3. Reconnect network | Graceful error handling with retry option |
| ERR-002 | Slow network | 1. Throttle network connection<br>2. Send message<br>3. Verify behavior | Loading indicator shown, request completes or times out gracefully |

### Input Validation

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| ERR-003 | Empty message handling | 1. Open chat widget<br>2. Try to send empty message | Submit button disabled or error message shown |
| ERR-004 | Very long message handling | 1. Open chat widget<br>2. Try to send extremely long message (>10,000 chars) | Message truncated or error message shown |
| ERR-005 | Special character handling | 1. Open chat widget<br>2. Send message with special characters | Message processed correctly without errors |

### File Handling Errors

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| ERR-006 | Unsupported file type | 1. Open chat widget<br>2. Try to upload unsupported file type | Clear error message shown |
| ERR-007 | Corrupted file | 1. Open chat widget<br>2. Try to upload corrupted file | Graceful error handling with clear message |
| ERR-008 | Very large file | 1. Open chat widget<br>2. Try to upload very large file (>25MB) | Clear error message about file size limit |

## Integration Tests

### ERPNext Integration

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| INT-001 | Sales Order integration | 1. Create Sales Order<br>2. Use Gemini to analyze order<br>3. Use Gemini to suggest actions | Correct analysis and suggestions provided |
| INT-002 | Purchase Order integration | 1. Create Purchase Order<br>2. Use Gemini to analyze order<br>3. Use Gemini to suggest actions | Correct analysis and suggestions provided |
| INT-003 | Customer integration | 1. Open Customer record<br>2. Use Gemini to analyze customer history<br>3. Ask for recommendations | Correct analysis and recommendations provided |

### Third-Party Integrations

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| INT-004 | Email integration | 1. Configure email action<br>2. Trigger workflow that sends email<br>3. Verify email delivery | Email sent successfully with correct content |
| INT-005 | PDF generation | 1. Request PDF report generation<br>2. Verify PDF content | PDF generated with correct content and formatting |

## Upgrade and Maintenance Tests

### Version Upgrade

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| UPG-001 | App upgrade | 1. Install previous version<br>2. Configure and use app<br>3. Upgrade to new version<br>4. Verify functionality | All functionality works correctly after upgrade |
| UPG-002 | Data migration | 1. Create data in previous version<br>2. Upgrade to new version<br>3. Verify data integrity | All data correctly migrated and accessible |

### Backup and Restore

| Test ID | Description | Steps | Expected Result |
|---------|-------------|-------|----------------|
| UPG-003 | Backup Gemini data | 1. Configure and use app<br>2. Backup ERPNext site<br>3. Verify backup contains Gemini data | Backup contains all Gemini-related data |
| UPG-004 | Restore Gemini data | 1. Restore from backup<br>2. Verify Gemini functionality<br>3. Verify data integrity | All functionality and data restored correctly |

## Test Execution Checklist

- [ ] All API Integration Tests
- [ ] All Chat Interface Tests
- [ ] All Context Awareness Tests
- [ ] All File Processing Tests
- [ ] All Workflow Automation Tests
- [ ] All Security Tests
- [ ] All Performance Tests
- [ ] All Edge Cases and Error Handling Tests
- [ ] All Integration Tests
- [ ] All Upgrade and Maintenance Tests

## Test Environment Requirements

- ERPNext v14.0.0 or higher
- Python 3.8+
- Valid Google Gemini API key
- Test user accounts with various permission levels
- Sample documents for testing (Sales Orders, Purchase Orders, etc.)
- Sample files for testing (images, PDFs, spreadsheets, etc.)
- Network throttling capability for performance testing
