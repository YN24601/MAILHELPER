import json
import tempfile
import unittest
from pathlib import Path

from mail_helper.email_pipeline import EmailPipeline


class EmailPipelineInputTest(unittest.TestCase):
    def test_load_emails_expands_mailbox_mapping(self):
        payload = {
            "account@example.com": [
                {"subject": "Test subject", "body": "Test body"}
            ]
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            input_file = Path(temporary_directory) / "fetched_emails.json"
            input_file.write_text(json.dumps(payload), encoding="utf-8")

            emails = EmailPipeline._load_emails(str(input_file))

        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]["mailbox"], "account@example.com")
        self.assertEqual(emails[0]["subject"], "Test subject")


if __name__ == "__main__":
    unittest.main()
