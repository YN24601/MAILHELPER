"""
Mailbox manager module for managing multiple email accounts
"""

import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
from .email_client import EmailClient

logger = logging.getLogger(__name__)


class MailboxManager:
    """
    Manages multiple mailbox connections and coordinates email fetching
    across multiple accounts.
    """

    def __init__(self):
        """Initialize the mailbox manager."""
        self.clients: Dict[str, EmailClient] = {}

    def add_mailbox(
        self, email_address: str, password: str, imap_server: str, imap_port: int = 993
    ) -> bool:
        """
        Add a new mailbox to manage.

        Args:
            email_address: Email address of the mailbox
            password: Password for the email account
            imap_server: IMAP server address
            imap_port: IMAP server port (default: 993)

        Returns:
            bool: True if mailbox was added and connected successfully
        """
        try:
            client = EmailClient(email_address, password, imap_server, imap_port)
            if client.connect():
                self.clients[email_address] = client
                logger.info(f"Added mailbox: {email_address}")
                return True
            else:
                logger.error(f"Failed to connect to mailbox: {email_address}")
                return False
        except Exception as e:
            logger.error(f"Error adding mailbox {email_address}: {e}")
            return False

    def remove_mailbox(self, email_address: str) -> None:
        """
        Remove a mailbox from management.

        Args:
            email_address: Email address to remove
        """
        if email_address in self.clients:
            self.clients[email_address].disconnect()
            del self.clients[email_address]
            logger.info(f"Removed mailbox: {email_address}")

    def disconnect_all(self) -> None:
        """Disconnect all mailboxes."""
        for email_address in list(self.clients.keys()):
            self.remove_mailbox(email_address)
        logger.info("All mailboxes disconnected")

    def get_unread_emails(
        self,
        mailbox: str = "INBOX",
        limit: Optional[int] = None,
        since_date: Optional[datetime] = None,
    ) -> Dict[str, List[Dict]]:
        """
        Fetch unread emails from all managed mailboxes.

        Args:
            mailbox: Mailbox name to fetch from (default: INBOX)
            limit: Maximum number of unread emails per mailbox
            since_date: Only fetch unread emails after this date

        Returns:
            Dict[str, List[Dict]]: Dictionary with email addresses as keys
                                   and lists of unread emails as values
        """
        all_emails = {}

        for email_address, client in self.clients.items():
            emails = client.fetch_unread_emails(mailbox, limit, since_date)
            all_emails[email_address] = emails
            logger.info(f"Fetched {len(emails)} unread emails from {email_address}")

        return all_emails

    def get_mailbox_list(self, email_address: str) -> List[str]:
        """
        Get list of mailboxes for a specific account.

        Args:
            email_address: Email address to query

        Returns:
            List[str]: List of mailbox names
        """
        if email_address in self.clients:
            return self.clients[email_address].get_mailboxes()
        return []

    def get_all_mailbox_lists(self) -> Dict[str, List[str]]:
        """
        Get mailbox lists for all accounts.

        Returns:
            Dict[str, List[str]]: Dictionary mapping email addresses to their mailboxes
        """
        mailbox_lists = {}
        for email_address, client in self.clients.items():
            mailbox_lists[email_address] = client.get_mailboxes()
        return mailbox_lists

    def save_emails_to_file(self, emails: Dict[str, List[Dict]], filename: str) -> bool:
        """
        Save fetched emails to a file (JSON format).

        Args:
            emails: Dictionary of emails from all mailboxes
            filename: Output filename

        Returns:
            bool: True if save was successful
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(emails, f, indent=2, default=str)
            logger.info(f"Emails saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving emails to file: {e}")
            return False

    def get_connected_accounts(self) -> List[str]:
        """
        Get list of connected email accounts.

        Returns:
            List[str]: List of email addresses
        """
        return list(self.clients.keys())
