"""
Main script to fetch emails from multiple mailboxes and analyze with AI.
"""

import json
import logging
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from mail_helper import MailboxManager
from mail_helper.analysis_models import AnalysisConfig
from mail_helper.email_pipeline import EmailPipeline
from mail_helper.report_generator import ReportGenerator

# Load environment variables
load_dotenv()


def _configure_logging() -> None:
    """Create the log path and configure file and console logging."""
    log_file = Path("logs") / "mail_helper.log"

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
    except FileNotFoundError as error:
        raise RuntimeError(
            f"Unable to create log file directory: {log_file.parent}"
        ) from error

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[file_handler, logging.StreamHandler()],
    )


# Configure logging
_configure_logging()

logger = logging.getLogger(__name__)


def load_config(config_file: str) -> dict:
    """Load mailbox configuration from JSON file."""
    try:
        with open(config_file, "r", encoding='utf-8') as f:
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

        # Initialize analysis config
        api_key = os.getenv('API_KEY')
        if not api_key:
            logger.error("API_KEY environment variable not set")
            return
        
        config = AnalysisConfig(
            model=settings.get('llm_model'),
            temperature=settings.get('llm_temperature'),
            max_tokens=settings.get('llm_max_tokens'),
            prompt_template=settings.get('analysis_prompt_template'),
            api_key=api_key,
        )
        
        # Run pipeline directly on the in-memory emails
        pipeline = EmailPipeline(config)
        results = pipeline.process_emails(
            emails_to_analyze,
            output_file=settings.get('analysis_output', 'analysis_results.json')
        )

        # Generate report
        report = ReportGenerator.generate_report(
            results,
            output_file=settings.get('report_output', 'email_analysis_report.md')
        )

        logger.info(f"Analysis complete. Generated report with {len(results)} analyzed emails")

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")


def _analyze_email_file(input_file: str, settings: dict) -> None:
    """Clean and analyze emails from an existing fetched email file."""
    try:
        api_key = os.getenv('API_KEY')
        if not api_key:
            logger.error("API_KEY environment variable not set")
            return

        config = AnalysisConfig(
            model=settings.get('llm_model'),
            temperature=settings.get('llm_temperature'),
            max_tokens=settings.get('llm_max_tokens'),
            prompt_template=settings.get('analysis_prompt_template'),
            api_key=api_key,
        )

        pipeline = EmailPipeline(config)
        results = pipeline.process_email_file(
            input_file,
            output_file=settings.get('analysis_output', 'analysis_results.json'),
        )

        ReportGenerator.generate_report(
            results,
            output_file=settings.get('report_output', 'email_analysis_report.md'),
        )
        logger.info(
            f"Analysis complete. Generated report with {len(results)} analyzed emails"
        )

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")


def main(analyze_file: Optional[str] = None):
    """Main function to fetch emails from multiple mailboxes."""

    # Load configuration
    config = load_config("config/mailboxes.json")
    if not config:
        logger.error("Failed to load configuration. Please check config/mailboxes.json")
        return

    settings = config.get("settings", {})

    if analyze_file:
        _analyze_email_file(analyze_file, settings)
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
    parser = argparse.ArgumentParser(description="Fetch and analyze mailbox emails")
    parser.add_argument(
        "--analyze-file",
        metavar="PATH",
        help="Analyze an existing fetched email JSON file without connecting to IMAP",
    )
    args = parser.parse_args()
    main(args.analyze_file)
