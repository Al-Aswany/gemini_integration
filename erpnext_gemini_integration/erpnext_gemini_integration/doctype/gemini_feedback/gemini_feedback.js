frappe.ui.form.on('Gemini Feedback', {
    refresh: function(frm) {
        // Add client-side logic here
    },
    
    validate: function(frm) {
        // Ensure rating is between 1 and 5
        if (frm.doc.rating < 1 || frm.doc.rating > 5) {
            frappe.throw(__('Rating must be between 1 and 5'));
        }
    }
}); 