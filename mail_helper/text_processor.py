"""
Text preprocessing module for email content.
"""

import re
from typing import Tuple
from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    """Strip HTML tags from content."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, data):
        self.fed.append(data)

    def get_data(self):
        return ''.join(self.fed)


class TextProcessor:
    """Process and clean email text content."""

    @staticmethod
    def strip_html(html_content: str) -> str:
        """Remove HTML tags and entities."""
        if not html_content:
            return ""
        stripper = HTMLStripper()
        try:
            stripper.feed(html_content)
            return stripper.get_data()
        except Exception:
            return html_content

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common email signatures
        signature_patterns = [
            r'--+\s*[\s\S]*',  # Lines starting with dashes
            r'Best regards[\s\S]*',
            r'Thanks[\s\S]*',
            r'Sent from.*',
        ]
        for pattern in signature_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        return text.strip()

    @staticmethod
    def extract_plain_text(email_data: dict) -> Tuple[str, str]:
        """Extract plain text from email (subject + body)."""
        subject = email_data.get('subject', '')
        
        # Try to get body from different possible fields
        body = email_data.get('body', '')
        if not body:
            body = email_data.get('text', '')
        if not body:
            body = email_data.get('html_body', '')

        # Strip HTML if present
        body = TextProcessor.strip_html(body)
        
        # Clean text
        body = TextProcessor.clean_text(body)
        
        return subject, body

    @staticmethod
    def prepare_for_analysis(email_data: dict) -> str:
        """Prepare email content for LLM analysis."""
        subject, body = TextProcessor.extract_plain_text(email_data)
        
        # Combine subject and body with clear separation
        prepared_text = f"Subject: {subject}\n\nBody: {body}"
        
        # Limit length to avoid excessive token usage
        max_chars = 2000
        if len(prepared_text) > max_chars:
            prepared_text = prepared_text[:max_chars] + "..."
        
        return prepared_text
