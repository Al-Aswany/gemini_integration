frappe.ui.form.on('Gemini Conversation', {
    refresh: function(frm) {
        // Add refresh button to load messages
        frm.add_custom_button(__('Refresh Messages'), function() {
            frm.reload_doc();
        });
    },
    
    validate: function(frm) {
        // Add validation logic here if needed
    },
    
    after_save: function(frm) {
        // Refresh the messages list after saving
        frm.reload_doc();
    }
}); 