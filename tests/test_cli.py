import context  # noqa: F401
import os
import tempfile
import unittest

from riskforge.cli import main


class CliTest(unittest.TestCase):
    def test_synth_then_validate(self):
        with tempfile.TemporaryDirectory() as d:
            rc = main([
                "data", "synth", "--out", d, "--days", "20",
                "--seed", "3", "--symbol", "DEMO",
            ])
            self.assertEqual(rc, 0)
            csv_path = os.path.join(d, "DEMO.csv")
            self.assertTrue(os.path.isfile(csv_path))

            rc = main(["data", "validate", "--file", csv_path])
            self.assertEqual(rc, 0)

    def test_validate_missing_file_rc2(self):
        rc = main(["data", "validate", "--file", os.path.join("no", "such.csv")])
        self.assertEqual(rc, 2)

    def test_multi_symbol_spec(self):
        with tempfile.TemporaryDirectory() as d:
            rc = main([
                "data", "synth", "--out", d, "--days", "10", "--seed", "2",
                "--symbol", "AAA", "--symbol", "BBB,50,0.05,0.35",
            ])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.isfile(os.path.join(d, "AAA.csv")))
            self.assertTrue(os.path.isfile(os.path.join(d, "BBB.csv")))


if __name__ == "__main__":
    unittest.main()
