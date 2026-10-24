import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tally.cli import main


class CliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"TALLY_FILE": str(Path(self.dir.name) / "l.json")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.dir.cleanup()

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(list(argv))
        return code, out.getvalue()

    def test_add_and_report(self):
        self.assertEqual(self.run_cli("add", "$4.50", "coffee")[0], 0)
        self.assertEqual(self.run_cli("add", "1,200", "rent", "--note", "october")[0], 0)
        code, text = self.run_cli("report")
        self.assertEqual(code, 0)
        self.assertIn("$1,200.00", text)
        self.assertIn("2 entries", text)

    def test_bad_amount_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_cli("add", "lots", "coffee")[0], 2)

    def test_export_csv(self):
        self.run_cli("add", "4.50", "coffee", "--date", "2026-10-01")
        code, text = self.run_cli("export")
        self.assertEqual(code, 0)
        self.assertEqual(text.splitlines()[0], "when,amount,category,note")
        self.assertIn("2026-10-01T00:00:00,4.50,coffee,", text)


if __name__ == "__main__":
    unittest.main()
