"""
Advanced example - Using MailHelper for various tasks
"""

from mail_helper import MailboxManager
from datetime import datetime, timedelta
import json


def example_1_basic_fetch():
    """Example 1: Basic unread email fetching from multiple accounts"""
    print("\n" + "="*60)
    print("Example 1: Basic Unread Email Fetching")
    print("="*60)

    manager = MailboxManager()

    # Add mailboxes
    manager.add_mailbox("email1@gmail.com", "app_password_1", "imap.gmail.com")
    manager.add_mailbox("email2@outlook.com", "app_password_2", "imap-mail.outlook.com")

    # Fetch unread emails
    emails = manager.get_unread_emails(limit=10)

    for email_address, email_list in emails.items():
        print(f"\n{email_address}: {len(email_list)} unread emails")
        for email in email_list[:3]:
            print(f"  • {email['subject']}")

    manager.disconnect_all()


def example_2_filter_by_date():
    """Example 2: Fetch unread emails from the last 7 days"""
    print("\n" + "="*60)
    print("Example 2: Filter Unread Emails by Date")
    print("="*60)

    manager = MailboxManager()
    manager.add_mailbox("your_email@gmail.com", "app_password", "imap.gmail.com")

    # Fetch unread emails from the last 7 days
    since_date = datetime.now() - timedelta(days=7)
    emails = manager.get_unread_emails(since_date=since_date)

    for email_address, email_list in emails.items():
        print(f"\nUnread emails from {email_address} (last 7 days): {len(email_list)}")

    manager.disconnect_all()


def example_3_explore_mailboxes():
    """Example 3: Explore available mailboxes"""
    print("\n" + "="*60)
    print("Example 3: Explore Available Mailboxes")
    print("="*60)

    manager = MailboxManager()
    manager.add_mailbox("your_email@gmail.com", "app_password", "imap.gmail.com")

    # Get all mailboxes for each account
    mailbox_lists = manager.get_all_mailbox_lists()

    for email_address, mailboxes in mailbox_lists.items():
        print(f"\n{email_address}:")
        for mailbox in mailboxes[:10]:  # Show first 10
            print(f"  • {mailbox}")

    manager.disconnect_all()


def example_4_fetch_specific_folder():
    """Example 4: Fetch unread emails from a specific mailbox folder"""
    print("\n" + "="*60)
    print("Example 4: Fetch Unread Emails from Specific Folder")
    print("="*60)

    manager = MailboxManager()
    manager.add_mailbox("your_email@gmail.com", "app_password", "imap.gmail.com")

    # Fetch unread emails from different folders
    folders = ["INBOX", "[Gmail]/Sent Mail", "[Gmail]/Drafts"]

    for folder in folders:
        emails = manager.get_unread_emails(mailbox=folder, limit=5)
        for email_address, email_list in emails.items():
            print(f"\n{folder}: {len(email_list)} unread emails")

    manager.disconnect_all()


def example_5_search_emails():
    """Example 5: Search and filter unread emails"""
    print("\n" + "="*60)
    print("Example 5: Search and Filter Unread Emails")
    print("="*60)

    manager = MailboxManager()
    manager.add_mailbox("your_email@gmail.com", "app_password", "imap.gmail.com")

    emails = manager.get_unread_emails(limit=50)

    # Filter emails by sender
    target_sender = "important@example.com"
    filtered = {}

    for email_address, email_list in emails.items():
        filtered_list = [e for e in email_list if target_sender in e["from"]]
        if filtered_list:
            filtered[email_address] = filtered_list
            print(f"\nFound {len(filtered_list)} emails from {target_sender}")
            for email in filtered_list:
                print(f"  • {email['subject']}")

    manager.disconnect_all()


def example_6_export_emails():
    """Example 6: Export unread emails to JSON"""
    print("\n" + "="*60)
    print("Example 6: Export Unread Emails to JSON")
    print("="*60)

    manager = MailboxManager()
    manager.add_mailbox("email1@gmail.com", "app_password_1", "imap.gmail.com")
    manager.add_mailbox("email2@outlook.com", "app_password_2", "imap-mail.outlook.com")

    # Fetch and save unread emails
    emails = manager.get_unread_emails(limit=20)
    manager.save_emails_to_file(emails, "exported_unread_emails.json")
    print("\nUnread emails exported to exported_unread_emails.json")

    manager.disconnect_all()


def example_7_get_statistics():
    """Example 7: Get unread email statistics"""
    print("\n" + "="*60)
    print("Example 7: Unread Email Statistics")
    print("="*60)

    manager = MailboxManager()
    manager.add_mailbox("your_email@gmail.com", "app_password", "imap.gmail.com")

    emails = manager.get_unread_emails(limit=100)

    stats = {
        "total_unread_emails": 0,
        "unread_emails_per_account": {},
        "top_senders": {},
    }

    for email_address, email_list in emails.items():
        stats["total_unread_emails"] += len(email_list)
        stats["unread_emails_per_account"][email_address] = len(email_list)

        # Count unread emails by sender
        for email in email_list:
            sender = email["from"].split("<")[-1].rstrip(">")
            stats["top_senders"][sender] = stats["top_senders"].get(sender, 0) + 1

    print(f"\nTotal unread emails: {stats['total_unread_emails']}")
    print(f"Unread emails per account: {stats['unread_emails_per_account']}")
    print("\nTop senders (unread):")
    for sender, count in sorted(stats["top_senders"].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  • {sender}: {count} unread emails")

    manager.disconnect_all()


def example_8_error_handling():
    """Example 8: Error handling and resilience"""
    print("\n" + "="*60)
    print("Example 8: Error Handling")
    print("="*60)

    manager = MailboxManager()

    # Try to add multiple mailboxes, some may fail
    mailboxes = [
        ("valid@gmail.com", "valid_password", "imap.gmail.com"),
        ("invalid@gmail.com", "wrong_password", "imap.gmail.com"),
        ("another@outlook.com", "another_password", "imap-mail.outlook.com"),
    ]

    successful = 0
    failed = 0

    for email, password, server in mailboxes:
        if manager.add_mailbox(email, password, server):
            successful += 1
        else:
            failed += 1

    print(f"\nSuccessfully connected: {successful}")
    print(f"Failed connections: {failed}")

    # Fetch from successful connections
    if manager.get_connected_accounts():
        emails = manager.get_unread_emails(limit=5)
        print(f"Fetched unread emails from {len(emails)} accounts")

    manager.disconnect_all()


if __name__ == "__main__":
    print("MailHelper - Advanced Examples")
    print("\nNote: Update the email/password/server credentials before running examples!")

    # Uncomment the examples you want to run:
    # example_1_basic_fetch()
    # example_2_filter_by_date()
    # example_3_explore_mailboxes()
    # example_4_fetch_specific_folder()
    # example_5_search_emails()
    # example_6_export_emails()
    # example_7_get_statistics()
    # example_8_error_handling()

    print("\nTo use these examples:")
    print("1. Update credentials in each example function")
    print("2. Uncomment the example you want to run")
    print("3. Run: python example_advanced.py")
