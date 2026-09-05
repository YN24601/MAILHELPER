# MailHelper

MailHelper is a smart email assistant that fetches unread emails from multiple mailboxes, analyzes them with AI, and generates a summary report.

## Config setup

- `config/mailboxes.json` - mailbox configuration file.
- `.env` - environment variables such as `API_KEY`.

To analyze an existing fetch without connecting to any mailbox, run:

```bash
conda run -n myenv python main.py --analyze-file fetched_emails.json
```

references:
    set up gmail password: https://support.google.com/accounts/answer/185833


## Output Files

- `logs/` - runtime logs are written here.
- `fetched_emails.json` - raw fetched email data when `save_emails` is enabled.
- `analysis_report.json` - AI analysis results when `enable_analysis` is enabled.
- `email_report.markdown` - final summary report for review.
