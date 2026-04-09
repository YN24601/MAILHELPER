"""
Email client module for connecting to IMAP servers and fetching emails
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EmailClient:
    def __init__(self, email_address: str, password: str, imap_server: str, imap_port: int = 993):
        """
        Initialize email client for a specific mailbox.

        Args:
            email_address: Email address of the mailbox
            password: Password for the email account
            imap_server: IMAP server address (e.g., imap.gmail.com)
            imap_port: IMAP server port (default: 993 for SSL)
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.imap = None
        self.is_connected = False

    def connect(self) -> bool:
        """
        Connect to the IMAP server.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap.login(self.email_address, self.password)

            #---- ID command to prevent trash emails for some servers ----
            imaplib.Commands['ID'] = ('AUTH') 
            args = ("name", "MailHelper", "version", "1.0.0", "vendor", "my-python-app")
            self.imap._command("ID", '("' + '" "'.join(args) + '")')
            #-------------------------------------------------------------

            self.is_connected = True
            logger.info(f"Successfully connected to {self.email_address}")
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP error for {self.email_address}: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Connection error for {self.email_address}: {e}")
            self.is_connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from the IMAP server."""
        if self.imap and self.is_connected:
            try:
                self.imap.close()
                self.imap.logout()
                self.is_connected = False
                logger.info(f"Disconnected from {self.email_address}")
            except Exception as e:
                logger.error(f"Error disconnecting from {self.email_address}: {e}")

    def get_mailboxes(self) -> List[str]:
        """
        Get list of available mailboxes.

        Returns:
            List[str]: List of mailbox names
        """
        if not self.is_connected:
            logger.warning("Not connected to IMAP server")
            return []

        try:
            status, mailboxes = self.imap.list()
            if status == "OK":
                # Parse mailbox names from the response
                mailbox_list = [mailbox.decode().split('"')[-2] for mailbox in mailboxes]
                return mailbox_list
            return []
        except Exception as e:
            logger.error(f"Error fetching mailboxes for {self.email_address}: {e}")
            return []

    def fetch_unread_emails(
        self,
        mailbox: str = "INBOX",
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Fetch unread emails from a specific mailbox.

        Args:
            mailbox: Mailbox name (default: INBOX)
            limit: Maximum number of unread emails to fetch
            since_date: Only fetch unread emails after this date

        Returns:
            List[Dict]: List of unread email dictionaries with keys: subject, from, to, date, body, html
        """
        if not self.is_connected:
            logger.warning("Not connected to IMAP server")
            return []

        try:
            # Select the mailbox
            status, _ = self.imap.select(mailbox, readonly=False) # readonly=False to mark emails as read when fetched
            if status != "OK":
                logger.warning(f"Could not select mailbox {mailbox}")
                logger.warning(f"Available mailboxes: {self.get_mailboxes()}")
                return []

            # Build search criteria - fetch only unread emails
            search_criteria = "UNSEEN"
            if since_date:
                date_str = since_date.strftime("%d-%b-%Y")
                search_criteria = f'UNSEEN SINCE "{date_str}"'

            # Search for emails
            status, email_ids = self.imap.search(None, search_criteria)
            if status != "OK":
                logger.warning(f"Could not search mailbox {mailbox}")
                return []

            email_list = email_ids[0].split()
            if limit:
                email_list = email_list[-limit:]  # Get most recent emails

            emails = []
            for email_id in email_list:
                status, msg_data = self.imap.fetch(email_id, "(RFC822)") 
                if status == "OK":
                    email_dict = self._parse_email(msg_data[0][1])
                    if email_dict:
                        emails.append(email_dict)

            logger.info(f"Fetched {len(emails)} unread emails from {self.email_address}/{mailbox}")
            return emails

        except Exception as e:
            logger.error(f"Error fetching unread emails from {self.email_address}/{mailbox}: {e}")
            return []

    def _parse_email(self, msg_bytes: bytes) -> Optional[Dict]:
        """
        Parse email message bytes into a dictionary.

        Args:
            msg_bytes: Raw email message bytes

        Returns:
            Dict: Parsed email dictionary or None if parsing fails
        """
        try:
            msg = email.message_from_bytes(msg_bytes)

            # Extract headers
            subject = self._decode_header(msg.get("Subject", "No Subject"))
            from_addr = self._decode_header(msg.get("From", "Unknown"))
            to_addr = self._decode_header(msg.get("To", "Unknown"))
            date_str = msg.get("Date", "Unknown")

            # Extract body
            body = ""
            html_body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get("Content-Disposition", "")

                    if "attachment" not in content_disposition:
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        elif content_type == "text/html":
                            html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            return {
                "subject": subject,
                "from": from_addr,
                "to": to_addr,
                "date": date_str,
                "body": body,
                "html": html_body,
            }

        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None

    @staticmethod
    def _decode_header(header_value: str) -> str:
        """
        Decode email header value.

        Args:
            header_value: Raw header value

        Returns:
            str: Decoded header value
        """
        try:
            decoded_parts = decode_header(header_value)
            decoded_str = ""
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    decoded_str += part.decode(charset or "utf-8", errors="ignore")
                else:
                    decoded_str += part
            return decoded_str
        except Exception:
            return header_value
