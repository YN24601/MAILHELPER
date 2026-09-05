import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_SCRIPT = PROJECT_ROOT / "main.py"


class LoggingSetupTest(unittest.TestCase):
    def test_main_creates_log_directory_and_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = subprocess.run(
                [sys.executable, str(MAIN_SCRIPT)],
                cwd=temporary_directory,
                env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                (Path(temporary_directory) / "logs" / "mail_helper.log").is_file()
            )


if __name__ == "__main__":
    unittest.main()
