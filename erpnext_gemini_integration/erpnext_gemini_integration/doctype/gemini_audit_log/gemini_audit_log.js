frappe.ui.form.on('Gemini Audit Log', {
    refresh: function(frm) {
        // Add client-side logic here
        frm.disable_save();
    },
    
    onload: function(frm) {
        // Add onload logic here if needed
    }
}); 