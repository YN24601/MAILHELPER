"""
Main script to fetch emails from multiple mailboxes
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from mail_helper import MailboxManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/mail_helper.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def load_config(config_file: str) -> dict:
    """Load mailbox configuration from JSON file."""
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_file}")
        return None


def main():
    """Main function to fetch emails from multiple mailboxes."""

    # Load configuration
    config = load_config("config/mailboxes.json")
    if not config:
        logger.error("Failed to load configuration. Please check config/mailboxes.json")
        return

    # Initialize mailbox manager
    manager = MailboxManager()

    # Add mailboxes from configuration
    logger.info("Adding mailboxes...")
    for mailbox_config in config.get("mailboxes", []):
        success = manager.add_mailbox(
            email_address=mailbox_config["email"],
            password=mailbox_config["password"],
            imap_server=mailbox_config["imap_server"],
            imap_port=mailbox_config.get("imap_port", 993),
        )
        if not success:
            logger.warning(f"Failed to add mailbox: {mailbox_config['email']}")

    # Get list of connected accounts
    connected_accounts = manager.get_connected_accounts()
    logger.info(f"Connected accounts: {connected_accounts}")

    if not connected_accounts:
        logger.error("No mailboxes were successfully connected")
        return

    # Fetch unread emails from INBOX
    logger.info("Fetching unread emails from INBOX...")
    settings = config.get("settings", {})
    fetch_limit = settings.get("fetch_limit", 20)

    all_emails = manager.get_unread_emails(mailbox="INBOX", limit=fetch_limit)

    # Display summary
    logger.info("\n" + "=" * 60)
    logger.info("UNREAD EMAIL FETCH SUMMARY")
    logger.info("=" * 60)

    total_emails = 0
    for email_address, emails in all_emails.items():
        logger.info(f"\n{email_address}: {len(emails)} unread emails")
        total_emails += len(emails)

        # Show all unreademails
        for i, email in enumerate(emails, 1):
            logger.info(f"  {i}. From: {email['from']}")
            logger.info(f"     Subject: {email['subject']}")
            logger.info(f"     Date: {email['date']}")


    logger.info(f"\nTotal unread emails fetched: {total_emails}")
    logger.info("=" * 60)

    # Save emails to file if configured
    if settings.get("save_emails", False):
        output_file = settings.get("output_file", "fetched_emails.json")
        manager.save_emails_to_file(all_emails, output_file)

    # Cleanup
    logger.info("\nDisconnecting from all mailboxes...")
    manager.disconnect_all()
    logger.info("Done!")


if __name__ == "__main__":
    main()
