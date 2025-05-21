frappe.ui.form.on('Gemini Sensitive Keyword', {
    refresh: function(frm) {
        // Add client-side logic here
    },
    
    validate: function(frm) {
        // Ensure keyword is not empty
        if (!frm.doc.keyword || !frm.doc.keyword.trim()) {
            frappe.throw(__('Keyword cannot be empty'));
        }
    }
}); 