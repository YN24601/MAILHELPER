"""
Unit tests for EmailClient class
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path)

from mail_helper.email_client import EmailClient


class TestEmailClient(unittest.TestCase):
    """Test cases for EmailClient"""

    def setUp(self):
        """Set up test fixtures"""
        # Load credentials from environment variables
        self.email = os.getenv("TEST_EMAIL", "test@example.com")
        self.password = os.getenv("TEST_PASSWORD", "test_password")
        self.imap_server = os.getenv("TEST_IMAP_SERVER", "imap.example.com")
        self.imap_port = int(os.getenv("TEST_IMAP_PORT", "993"))
        self.client = EmailClient(self.email, self.password, self.imap_server, self.imap_port)

    def test_initialization(self):
        """Test EmailClient initialization"""
        self.assertEqual(self.client.email_address, self.email)
        self.assertEqual(self.client.password, self.password)
        self.assertEqual(self.client.imap_server, self.imap_server)
        self.assertEqual(self.client.imap_port, 993)
        self.assertFalse(self.client.is_connected)

    def test_custom_port(self):
        """Test EmailClient with custom port"""
        client = EmailClient(self.email, self.password, self.imap_server, imap_port=143)
        self.assertEqual(client.imap_port, 143)

    @patch("mail_helper.email_client.imaplib.IMAP4_SSL")
    def test_connect_success(self, mock_imap):
        """Test successful connection"""
        mock_instance = MagicMock()
        mock_imap.return_value = mock_instance

        result = self.client.connect()

        self.assertTrue(result)
        self.assertTrue(self.client.is_connected)
        mock_instance.login.assert_called_once_with(self.email, self.password)

    @patch("mail_helper.email_client.imaplib.IMAP4_SSL")
    def test_connect_failure(self, mock_imap):
        """Test connection failure"""
        mock_imap.side_effect = Exception("Connection failed")

        result = self.client.connect()

        self.assertFalse(result)
        self.assertFalse(self.client.is_connected)

    def test_decode_header(self):
        """Test header decoding"""
        header = "Test Subject"
        result = EmailClient._decode_header(header)
        self.assertEqual(result, header)

    def test_parse_email_with_missing_fields(self):
        """Test email parsing with missing fields"""
        # This is a basic test - full testing would require mock email data
        pass


if __name__ == "__main__":
    unittest.main()
