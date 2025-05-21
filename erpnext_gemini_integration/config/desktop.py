# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from frappe import _

def get_data():
    return [
        {
            "module_name": "ERPNext Gemini Integration",
            "color": "blue",
            "icon": "octicon octicon-file-directory",
            "type": "module",
            "label": _("Gemini AI")
        }
    ]
