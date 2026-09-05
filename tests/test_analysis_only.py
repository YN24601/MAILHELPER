import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from mail_helper.email_pipeline import EmailPipeline
from mail_helper.report_generator import ReportGenerator


class AnalysisOnlyModeTest(unittest.TestCase):
    def test_analysis_only_mode_does_not_connect_to_mailboxes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_file = Path(temporary_directory) / "fetched_emails.json"
            input_file.write_text("{}", encoding="utf-8")

            with (
                patch.dict(os.environ, {"API_KEY": "test-key"}),
                patch("main.MailboxManager") as mailbox_manager,
                patch.object(EmailPipeline, "process_email_file", return_value=[]) as process,
                patch.object(ReportGenerator, "generate_report"),
            ):
                main.main(str(input_file))

        mailbox_manager.assert_not_called()
        process.assert_called_once_with(
            str(input_file), output_file="analysis_report.json"
        )


if __name__ == "__main__":
    unittest.main()
