"""
Main script to fetch emails from multiple mailboxes and analyze with AI.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from mail_helper import MailboxManager
from mail_helper.analysis_models import AnalysisConfig
from mail_helper.email_pipeline import EmailPipeline
from mail_helper.report_generator import ReportGenerator

# Load environment variables
load_dotenv()

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


def _analyze_emails(all_emails: dict, settings: dict) -> None:
    """Analyze fetched emails using AI."""
    try:
        # Collect all emails into a single list, preserving mailbox info
        emails_to_analyze = []
        for email_address, emails in all_emails.items():
            for email in emails:
                email['mailbox'] = email_address
            emails_to_analyze.extend(emails)
        
        if not emails_to_analyze:
            logger.warning("No emails to analyze")
            return
        
        # Save emails to temporary file for analysis
        temp_file = "temp_emails_for_analysis.json"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(emails_to_analyze, f, ensure_ascii=False, indent=2)
        
        # Initialize analysis config
        api_key = os.getenv('API_KEY')
        if not api_key:
            logger.error("API_KEY environment variable not set")
            return
        
        config = AnalysisConfig(
            model=settings.get('llm_model'),
            temperature=settings.get('llm_temperature', 0.7),
            api_key=api_key
        )
        
        # Run pipeline
        pipeline = EmailPipeline(config)
        results = pipeline.process_email_file(
            temp_file,
            output_file=settings.get('analysis_output', 'analysis_results.json')
        )
        
        # Generate report
        report = ReportGenerator.generate_report(
            results,
            output_file=settings.get('report_output', 'email_analysis_report.md')
        )
        
        logger.info(f"Analysis complete. Generated report with {len(results)} analyzed emails")
        
        # Clean up temp file
        Path(temp_file).unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")



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
    fetch_limit = settings.get("fetch_limit", 50)

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

    # AI analysis if enabled
    if settings.get("enable_analysis", False):
        logger.info("\nStarting AI email analysis...")
        _analyze_emails(all_emails, settings)

    # Cleanup
    logger.info("\nDisconnecting from all mailboxes...")
    manager.disconnect_all()
    logger.info("Done!")


if __name__ == "__main__":
    main()
