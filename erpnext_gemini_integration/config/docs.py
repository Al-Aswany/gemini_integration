# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from frappe import _

def get_data():
    return [
        {
            "label": _("Gemini AI"),
            "icon": "octicon octicon-file-directory",
            "items": [
                {
                    "type": "doctype",
                    "name": "Gemini Assistant Settings",
                    "description": _("Configure Gemini AI integration settings"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Gemini Conversation",
                    "description": _("View and manage AI conversations"),
                },
                {
                    "type": "doctype",
                    "name": "Gemini Audit Log",
                    "description": _("View AI interaction audit logs"),
                },
                {
                    "type": "doctype",
                    "name": "Gemini Sensitive Keyword",
                    "description": _("Configure sensitive data masking"),
                },
                {
                    "type": "doctype",
                    "name": "Gemini Feedback",
                    "description": _("User feedback on AI responses"),
                }
            ]
        },
        {
            "label": _("Documentation"),
            "icon": "octicon octicon-book",
            "items": [
                {
                    "type": "page",
                    "name": "gemini-docs",
                    "label": _("Gemini AI Documentation"),
                    "link": "https://github.com/Al-Aswany/gemini_integration",
                    "description": _("Documentation for Gemini AI integration"),
                }
            ]
        }
    ]
