frappe.ui.form.on('Gemini Message', {
    // refresh: function(frm) {
    //     // Add feedback button if no feedback exists
    //     if (!frm.doc.feedback_rating) {
    //         frm.add_custom_button(__('Add Feedback'), function() {
    //             frappe.new_doc('Gemini Feedback', {
    //                 message: frm.doc.name
    //             });
    //         });
    //     }
    // },
    
    // validate: function(frm) {
    //     // Ensure message is not empty
    //     if (!frm.doc.message || !frm.doc.message.trim()) {
    //         frappe.throw(__('Message cannot be empty'));
    //     }
    // }
}); 