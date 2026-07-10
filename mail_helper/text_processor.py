"""
Text preprocessing module for email content.
"""

import re
from typing import Tuple
from bs4 import BeautifulSoup

# Precompiled patterns (reused across every email instead of recompiling per call)
_WHITESPACE = re.compile(r'\s+')
_SIGNATURE_PATTERNS = [
    re.compile(r'--+\s*[\s\S]*', re.IGNORECASE),  # Lines starting with dashes
    re.compile(r'Best regards[\s\S]*', re.IGNORECASE),
    re.compile(r'Thanks[\s\S]*', re.IGNORECASE),
    re.compile(r'Sent from.*', re.IGNORECASE),
]


class TextProcessor:
    """Process and clean email text content."""

    @staticmethod
    def strip_html(html_content: str) -> str:
        """Remove HTML tags and entities using BeautifulSoup."""
        if not html_content:
            return ""
        try:
            # html.parser is pure-stdlib and does not raise on malformed HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            return _WHITESPACE.sub(' ', text).strip()
        except Exception:
            return html_content

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""

        # Remove extra whitespace
        text = _WHITESPACE.sub(' ', text)

        # Remove common email signatures
        for pattern in _SIGNATURE_PATTERNS:
            text = pattern.sub('', text)

        return text.strip()

    @staticmethod
    def extract_plain_text(email_data: dict) -> Tuple[str, str]:
        """Extract plain text from email (subject + body)."""
        subject = email_data.get('subject', '')

        # Try body fields in order of preference
        body = email_data.get('body') or email_data.get('text') or email_data.get('html_body') or ''

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
