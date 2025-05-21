// Chat Widget JavaScript
frappe.provide("erpnext_gemini_integration.chat");

erpnext_gemini_integration.chat = {
    // Configuration
    config: {
        active_conversation: null,
        is_minimized: false,
        is_expanded: false,
        file_attachment: null,
        context: {},
        typing_timeout: null
    },
    
    // Initialization
    init: function() {
        this.load_template();
        this.bind_events();
        this.check_context();
    },
    
    // Load the chat widget template
    load_template: function() {
        var me = this;
        
        frappe.call({
            method: "frappe.client.get_html",
            args: {
                doc: {
                    doctype: "Page",
                    name: "gemini-chat"
                },
                name: "gemini-chat"
            },
            callback: function(r) {
                if (r.message) {
                    $(document.body).append(r.message);
                    me.post_template_load();
                } else {
                    // Fallback to direct template loading
                    frappe.require([
                        "/assets/erpnext_gemini_integration/templates/chat_widget.html"
                    ], function() {
                        var template = frappe.render_template("chat_widget");
                        $(document.body).append(template);
                        me.post_template_load();
                    });
                }
            }
        });
    },
    
    // Actions after template is loaded
    post_template_load: function() {
        // Show the chat widget
        $("#gemini-chat-widget").addClass("fade-in");
        
        // Load active conversations
        this.load_conversations();
        
        // Auto-resize textarea
        this.setup_auto_resize();
    },
    
    // Bind events to chat widget elements
    bind_events: function() {
        var me = this;
        
        // Chat controls
        $(document).on("click", "#chat-minimize", function() {
            me.minimize_chat();
        });
        
        $(document).on("click", "#chat-expand", function() {
            me.toggle_expand_chat();
        });
        
        $(document).on("click", "#chat-close", function() {
            me.close_chat();
        });
        
        $(document).on("click", "#chat-launcher", function() {
            me.restore_chat();
        });
        
        // Message sending
        $(document).on("click", "#chat-send", function() {
            me.send_message();
        });
        
        $(document).on("keydown", "#chat-input", function(e) {
            if (e.keyCode === 13 && !e.shiftKey) {
                e.preventDefault();
                me.send_message();
            }
        });
        
        // File attachment
        $(document).on("click", "#chat-attach", function() {
            me.open_file_dialog();
        });
        
        $(document).on("click", "#file-remove", function() {
            me.remove_attachment();
        });
        
        // Conversation list
        $(document).on("click", "#conversation-close", function() {
            me.hide_conversation_list();
        });
        
        $(document).on("click", "#new-conversation", function() {
            me.start_new_conversation();
        });
        
        $(document).on("click", ".conversation-item", function() {
            var conversation_id = $(this).data("id");
            me.load_conversation(conversation_id);
        });
        
        // Feedback
        $(document).on("click", ".message-feedback", function() {
            var message_id = $(this).data("message-id");
            me.show_feedback_dialog(message_id);
        });
        
        $(document).on("click", "#feedback-close", function() {
            me.hide_feedback_dialog();
        });
        
        $(document).on("click", "#feedback-positive, #feedback-negative", function() {
            $(".feedback-rating button").removeClass("btn-primary").addClass("btn-default");
            $(this).removeClass("btn-default").addClass("btn-primary");
        });
        
        $(document).on("click", "#submit-feedback", function() {
            me.submit_feedback();
        });
    },
    
    // Check current page context
    check_context: function() {
        var me = this;
        
        // Get current doctype and docname if available
        if (frappe.get_route_str().indexOf("Form/") === 0) {
            var route = frappe.get_route();
            if (route.length >= 3) {
                me.config.context = {
                    doctype: route[1],
                    docname: route[2]
                };
                
                // Update context info in chat widget
                $("#chat-context-info").text("Context: " + route[1] + " - " + route[2]);
            }
        }
    },
    
    // Send a message to the assistant
    send_message: function() {
        var me = this;
        var input = $("#chat-input");
        var message = input.val().trim();
        
        if (!message) return;
        
        // Clear input
        input.val("");
        this.resize_input();
        
        // Add message to chat
        this.add_message("user", message);
        
        // Show typing indicator
        this.show_typing_indicator();
        
        // Prepare context
        var context = me.config.context;
        
        // Send to API
        frappe.call({
            method: "erpnext_gemini_integration.api.chat_api.send_message",
            args: {
                conversation_id: me.config.active_conversation,
                message: message,
                context: context
            },
            callback: function(r) {
                // Hide typing indicator
                me.hide_typing_indicator();
                
                if (r.message && r.message.success) {
                    // Update active conversation
                    me.config.active_conversation = r.message.conversation_id;
                    
                    // Add response to chat
                    me.add_message("assistant", r.message.response, r.message.message_id);
                    
                    // Scroll to bottom
                    me.scroll_to_bottom();
                } else {
                    // Show error
                    me.add_message("system", "Sorry, I encountered an error. Please try again.");
                }
            }
        });
        
        // Scroll to bottom
        this.scroll_to_bottom();
    },
    
    // Add a message to the chat
    add_message: function(role, content, message_id) {
        var message_html = `
            <div class="chat-message ${role}">
                <div class="message-content">
                    <p>${this.format_message(content)}</p>
                </div>
                ${role === "assistant" ? `
                <div class="message-actions">
                    <button class="message-feedback" data-message-id="${message_id}">
                        <i class="fa fa-thumbs-up"></i> Feedback
                    </button>
                </div>
                ` : ""}
                <div class="message-timestamp">
                    ${this.format_time(new Date())}
                </div>
            </div>
        `;
        
        $("#chat-messages").append(message_html);
        this.scroll_to_bottom();
    },
    
    // Format message content with markdown
    format_message: function(content) {
        if (!content) return "";
        
        // Convert markdown to HTML
        try {
            // Basic markdown formatting
            var formatted = content
                // Code blocks
                .replace(/```([\s\S]*?)```/g, function(match, code) {
                    return '<pre><code>' + code.trim() + '</code></pre>';
                })
                // Inline code
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                // Bold
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                // Italic
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                // Links
                .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
                // Lists
                .replace(/^\s*[\-\*]\s+(.*?)$/gm, '<li>$1</li>')
                .replace(/(<li>.*?<\/li>\n)+/g, '<ul>$&</ul>')
                // Headers
                .replace(/^### (.*?)$/gm, '<h5>$1</h5>')
                .replace(/^## (.*?)$/gm, '<h4>$1</h4>')
                .replace(/^# (.*?)$/gm, '<h3>$1</h3>')
                // Paragraphs
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');
            
            return '<p>' + formatted + '</p>';
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
        var indicator = `
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
        var chat_body = $(".chat-body");
        chat_body.scrollTop(chat_body[0].scrollHeight);
    },
    
    // Load active conversations
    load_conversations: function() {
        var me = this;
        
        frappe.call({
            method: "erpnext_gemini_integration.api.chat_api.get_active_conversations",
            callback: function(r) {
                if (r.message && r.message.length) {
                    // Clear conversation list
                    $("#conversation-items").empty();
                    
                    // Add conversations to list
                    $.each(r.message, function(i, conv) {
                        var context_info = conv.context_doctype ? 
                            `<div class="conversation-context">${conv.context_doctype} - ${conv.context_docname || ""}</div>` : "";
                        
                        var item = `
                            <div class="conversation-item" data-id="${conv.name}">
                                <div class="conversation-title">Conversation ${i+1}</div>
                                ${context_info}
                                <div class="conversation-preview">${conv.last_message}</div>
                                <div class="conversation-time">${me.format_date(conv.last_updated)}</div>
                            </div>
                        `;
                        
                        $("#conversation-items").append(item);
                    });
                    
                    // Load the most recent conversation
                    if (!me.config.active_conversation) {
                        me.load_conversation(r.message[0].name);
                    }
                } else {
                    // Start a new conversation
                    me.start_new_conversation();
                }
            }
        });
    },
    
    // Load a specific conversation
    load_conversation: function(conversation_id) {
        var me = this;
        
        frappe.call({
            method: "erpnext_gemini_integration.api.chat_api.get_conversation_history",
            args: {
                conversation_id: conversation_id,
                format_type: "html"
            },
            callback: function(r) {
                if (r.message) {
                    // Set active conversation
                    me.config.active_conversation = conversation_id;
                    
                    // Clear chat messages
                    $("#chat-messages").empty();
                    
                    // Add welcome message if no history
                    if (!r.message.trim()) {
                        me.add_message("system", "Hello! I'm your Gemini AI assistant. How can I help you today?");
                    } else {
                        // Add conversation history
                        $("#chat-messages").html(r.message);
                    }
                    
                    // Hide conversation list
                    me.hide_conversation_list();
                    
                    // Scroll to bottom
                    me.scroll_to_bottom();
                }
            }
        });
    },
    
    // Start a new conversation
    start_new_conversation: function() {
        // Reset active conversation
        this.config.active_conversation = null;
        
        // Clear chat messages
        $("#chat-messages").empty();
        
        // Add welcome message
        this.add_message("system", "Hello! I'm your Gemini AI assistant. How can I help you today?");
        
        // Hide conversation list
        this.hide_conversation_list();
    },
    
    // Show conversation list
    show_conversation_list: function() {
        $("#gemini-conversation-list").show().addClass("fade-in");
    },
    
    // Hide conversation list
    hide_conversation_list: function() {
        $("#gemini-conversation-list").hide();
    },
    
    // Format date
    format_date: function(date_str) {
        var date = new Date(date_str);
        return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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
    
    // Toggle expanded state
    toggle_expand_chat: function() {
        if (this.config.is_expanded) {
            // Restore to normal size
            $("#gemini-chat-widget").css({
                width: "350px",
                height: "500px",
                top: "auto",
                left: "auto",
                transform: "none"
            });
            $("#chat-expand i").removeClass("fa-compress").addClass("fa-expand");
        } else {
            // Expand to full screen
            $("#gemini-chat-widget").css({
                width: "80%",
                height: "80%",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)"
            });
            $("#chat-expand i").removeClass("fa-expand").addClass("fa-compress");
        }
        
        this.config.is_expanded = !this.config.is_expanded;
        this.scroll_to_bottom();
    },
    
    // Close chat
    close_chat: function() {
        $("#gemini-chat-widget").hide();
        $("#chat-launcher").hide();
    },
    
    // Open file dialog
    open_file_dialog: function() {
        var me = this;
        
        // Create file input
        var file_input = $('<input type="file" accept="image/*,.pdf,.csv,.txt,.json,.xlsx">');
        
        // Handle file selection
        file_input.on("change", function() {
            var file = this.files[0];
            if (file) {
                me.handle_file_selection(file);
            }
        });
        
        // Trigger click
        file_input.click();
    },
    
    // Handle file selection
    handle_file_selection: function(file) {
        var me = this;
        
        // Store file
        me.config.file_attachment = file;
        
        // Show file preview
        $("#file-name").text(file.name);
        $("#chat-file-preview").show();
        
        // Upload file
        var form_data = new FormData();
        form_data.append("file", file);
        
        $.ajax({
            url: "/api/method/upload_file",
            type: "POST",
            data: form_data,
            processData: false,
            contentType: false,
            success: function(r) {
                if (r.message) {
                    // Store file URL
                    me.config.file_url = r.message.file_url;
                    
                    // Add file info to context
                    me.config.context.file_url = r.message.file_url;
                    me.config.context.file_name = file.name;
                    me.config.context.file_type = file.type;
                }
            },
            error: function() {
                frappe.msgprint(__("Error uploading file. Please try again."));
                me.remove_attachment();
            }
        });
    },
    
    // Remove attachment
    remove_attachment: function() {
        this.config.file_attachment = null;
        this.config.file_url = null;
        
        // Remove file info from context
        delete this.config.context.file_url;
        delete this.config.context.file_name;
        delete this.config.context.file_type;
        
        // Hide file preview
        $("#chat-file-preview").hide();
    },
    
    // Show feedback dialog
    show_feedback_dialog: function(message_id) {
        // Store message ID
        this.config.feedback_message_id = message_id;
        
        // Get message content
        var message_content = $(".chat-message .message-actions button[data-message-id='" + message_id + "']")
            .closest(".chat-message")
            .find(".message-content")
            .html();
        
        // Set message in dialog
        $("#feedback-message").html(message_content);
        
        // Reset feedback options
        $(".feedback-rating button").removeClass("btn-primary").addClass("btn-default");
        $("#feedback-comments").val("");
        
        // Show dialog
        $("#gemini-feedback-dialog").show().addClass("fade-in");
    },
    
    // Hide feedback dialog
    hide_feedback_dialog: function() {
        $("#gemini-feedback-dialog").hide();
    },
    
    // Submit feedback
    submit_feedback: function() {
        var me = this;
        var message_id = this.config.feedback_message_id;
        
        // Get rating
        var rating = $("#feedback-positive").hasClass("btn-primary") ? "Positive" : 
                    $("#feedback-negative").hasClass("btn-primary") ? "Negative" : null;
        
        if (!rating) {
            frappe.msgprint(__("Please select a rating."));
            return;
        }
        
        // Get comments
        var comments = $("#feedback-comments").val();
        
        // Submit feedback
        frappe.call({
            method: "erpnext_gemini_integration.api.chat_api.submit_feedback",
            args: {
                message_id: message_id,
                rating: rating,
                comments: comments
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    // Hide dialog
                    me.hide_feedback_dialog();
                    
                    // Show confirmation
                    frappe.show_alert({
                        message: __("Thank you for your feedback!"),
                        indicator: "green"
                    });
                    
                    // Update feedback button
                    $(".message-actions button[data-message-id='" + message_id + "']")
                        .html('<i class="fa fa-check"></i> Feedback submitted');
                } else {
                    frappe.msgprint(__("Error submitting feedback. Please try again."));
                }
            }
        });
    },
    
    // Setup auto-resize for textarea
    setup_auto_resize: function() {
        var me = this;
        
        $(document).on("input", "#chat-input", function() {
            me.resize_input();
        });
    },
    
    // Resize input textarea
    resize_input: function() {
        var input = $("#chat-input")[0];
        if (!input) return;
        
        // Reset height
        input.style.height = "auto";
        
        // Set new height based on content
        var new_height = Math.min(input.scrollHeight, 100);
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
