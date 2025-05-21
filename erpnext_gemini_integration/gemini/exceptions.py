# -*- coding: utf-8 -*-
# Copyright (c) 2025, Al-Aswany and contributors
# For license information, please see license.txt

class GeminiAPIError(Exception):
    """Base exception class for Gemini API errors."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class GeminiRateLimitError(GeminiAPIError):
    """Exception raised when Gemini API rate limits are exceeded."""
    pass


class GeminiAuthError(GeminiAPIError):
    """Exception raised when there are authentication issues with Gemini API."""
    pass

class GeminiError(Exception):
    """Base for all Gemini-related errors."""
    pass

class GeminiWorkflowError(GeminiError):
    """
    Raised when a workflow step fails or returns an unexpected response.
    """
    pass

class GeminiContentFilterError(GeminiAPIError):
    """Exception raised when content is filtered by Gemini API safety settings."""
    pass


class GeminiContextError(GeminiAPIError):
    """Exception raised when there are issues with context management."""
    pass


class GeminiFileProcessingError(GeminiAPIError):
    """Exception raised when there are issues processing files."""
    pass


class GeminiSecurityError(GeminiAPIError):
    """Exception raised when there are security-related issues."""
    pass
