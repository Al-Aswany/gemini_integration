// Simplified Chat Widget JavaScript
frappe.provide("erpnext_gemini_integration.chat");

erpnext_gemini_integration.chat = {
    // Configuration
    config: {
        active_conversation: null,
        is_minimized: false,
        file_attachment: null,
        context: {}
    },
    
    // Initialization
    init: function() {
        const template = '/assets/erpnext_gemini_integration/templates/chat_widget.html';
        
        // Load template
        $.ajax({
            url: template,
            type: 'GET',
            dataType: 'html',
            success: (data) => {
                $(document.body).append(data);
                this.post_init();
            },
            error: () => {
                console.error("Failed to load chat widget template");
            }
        });
    },
    
    // Actions after template is loaded
    post_init: function() {
        // Show chat widget with fade effect
        $("#gemini-chat-widget").addClass("fade-in");
        
        // Get current context (doctype and docname)
        this.check_context();
        
        // Bind all event handlers
        this.bind_events();
        
        // Auto-resize textarea
        this.setup_auto_resize();
    },
    
    // Bind events to chat widget elements
    bind_events: function() {
        const me = this;
        
        // Chat controls
        $(document).on("click", "#chat-minimize", () => this.minimize_chat());
        $(document).on("click", "#chat-close", () => this.close_chat());
        $(document).on("click", "#chat-launcher button", () => this.restore_chat());
        
        // Message sending
        $(document).on("click", "#chat-send", () => this.send_message());
        $(document).on("keydown", "#chat-input", function(e) {
            if (e.keyCode === 13 && !e.shiftKey) {
                e.preventDefault();
                me.send_message();
            }
        });
        
        // File attachment
        $(document).on("click", "#chat-attach", () => this.open_file_dialog());
        $(document).on("click", "#file-remove", () => this.remove_attachment());
    },
    
    // Check current page context
    check_context: function() {
        // Get current doctype and docname if available
        if (frappe.get_route_str().indexOf("Form/") === 0) {
            const route = frappe.get_route();
            if (route.length >= 3) {
                this.config.context = {
                    doctype: route[1],
                    docname: route[2]
                };
                
                // Update context info in chat widget
                $("#chat-context-info").text(`Context: ${route[1]} - ${route[2]}`);
            }
        }
    },
    
    // Send a message to the assistant
    send_message: function() {
        const input = $("#chat-input");
        const message = input.val().trim();
        
        if (!message) return;
        
        // Clear input
        input.val("");
        this.resize_input();
        
        // Add message to chat
        this.add_message("user", message);
        
        // Show typing indicator
        this.show_typing_indicator();
        
        // Send to API
        frappe.call({
            method: "erpnext_gemini_integration.api.chat_api.send_message",
            args: {
                conversation_id: this.config.active_conversation,
                message: message,
                context: this.config.context
            },
            callback: (r) => {
                // Hide typing indicator
                this.hide_typing_indicator();
                
                if (r.message && r.message.success) {
                    // Update active conversation
                    this.config.active_conversation = r.message.conversation_id;
                    
                    // Add response to chat
                    this.add_message("assistant", r.message.response, r.message.message_id);
                } else {
                    // Show error
                    this.add_message("system", "Sorry, I encountered an error. Please try again.");
                }
                
                // Scroll to bottom
                this.scroll_to_bottom();
            }
        });
        
        // Scroll to bottom
        this.scroll_to_bottom();
    },
    
    // Add a message to the chat
    add_message: function(role, content, message_id) {
        const message_html = `
            <div class="chat-message ${role}">
                <div class="message-content">
                    <p>${this.format_message(content)}</p>
                </div>
                <div class="message-timestamp">
                    ${this.format_time(new Date())}
                </div>
            </div>
        `;
        
        $("#chat-messages").append(message_html);
        this.scroll_to_bottom();
    },
    
    // Format message content with basic markdown
    format_message: function(content) {
        if (!content) return "";
        
        try {
            // Basic markdown formatting
            const formatted = content
                // Code blocks
                .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
                // Inline code
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                // Bold
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                // Italic
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                // Links
                .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
                // Line breaks
                .replace(/\n/g, '<br>');
            
            return formatted;
        } catch (e) {
            console.error("Error formatting message:", e);
            return content;
        }
    },
    
    // Format timestamp
    format_time: function(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    
    // Show typing indicator
    show_typing_indicator: function() {
        const indicator = `
            <div class="typing-indicator" id="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        $("#chat-messages").append(indicator);
        this.scroll_to_bottom();
    },
    
    // Hide typing indicator
    hide_typing_indicator: function() {
        $("#typing-indicator").remove();
    },
    
    // Scroll chat to bottom
    scroll_to_bottom: function() {
        const chat_body = $(".chat-body");
        chat_body.scrollTop(chat_body[0].scrollHeight);
    },
    
    // Minimize chat
    minimize_chat: function() {
        $("#gemini-chat-widget").hide();
        $("#chat-launcher").show().addClass("fade-in");
        this.config.is_minimized = true;
    },
    
    // Restore chat from minimized state
    restore_chat: function() {
        $("#chat-launcher").hide();
        $("#gemini-chat-widget").show().addClass("fade-in");
        this.config.is_minimized = false;
        this.scroll_to_bottom();
    },
    
    // Close chat
    close_chat: function() {
        $("#gemini-chat-widget").hide();
        $("#chat-launcher").hide();
    },
    
    // Open file dialog
    open_file_dialog: function() {
        // Create file input
        const file_input = $('<input type="file" accept="image/*,.pdf,.csv,.txt,.json,.xlsx">');
        
        // Handle file selection
        file_input.on("change", () => {
            const file = file_input[0].files[0];
            if (file) {
                this.handle_file_selection(file);
            }
        });
        
        // Trigger click
        file_input.click();
    },
    
    // Handle file selection
    handle_file_selection: function(file) {
        // Store file
        this.config.file_attachment = file;
        
        // Show file preview
        $("#file-name").text(file.name);
        $("#chat-file-preview").show();
        
        // Upload file
        const form_data = new FormData();
        form_data.append("file", file);
        
        $.ajax({
            url: "/api/method/upload_file",
            type: "POST",
            data: form_data,
            processData: false,
            contentType: false,
            success: (r) => {
                if (r.message) {
                    // Add file info to context
                    this.config.context.file_url = r.message.file_url;
                    this.config.context.file_name = file.name;
                    this.config.context.file_type = file.type;
                }
            },
            error: () => {
                frappe.msgprint(__("Error uploading file. Please try again."));
                this.remove_attachment();
            }
        });
    },
    
    // Remove attachment
    remove_attachment: function() {
        this.config.file_attachment = null;
        
        // Remove file info from context
        delete this.config.context.file_url;
        delete this.config.context.file_name;
        delete this.config.context.file_type;
        
        // Hide file preview
        $("#chat-file-preview").hide();
    },
    
    // Setup auto-resize for textarea
    setup_auto_resize: function() {
        $(document).on("input", "#chat-input", () => this.resize_input());
    },
    
    // Resize input textarea
    resize_input: function() {
        const input = $("#chat-input")[0];
        if (!input) return;
        
        // Reset height
        input.style.height = "auto";
        
        // Set new height based on content (max 100px)
        const new_height = Math.min(input.scrollHeight, 100);
        input.style.height = new_height + "px";
    }
};

// Initialize chat widget when Frappe is ready
$(document).on("app_ready", function() {
    // Initialize after a short delay to ensure all resources are loaded
    setTimeout(function() {
        erpnext_gemini_integration.chat.init();
    }, 1000);
});