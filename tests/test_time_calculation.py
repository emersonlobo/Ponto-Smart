import unittest
import pandas as pd

from utils import calculate_total_hours, generate_pdf_report


class TimeCalculationTests(unittest.TestCase):
    def test_calculate_total_hours_between_entry_and_exit(self):
        df = pd.DataFrame([
            {"timestamp": "2024-01-01T08:00:00-03:00", "action": "entrada"},
            {"timestamp": "2024-01-01T17:30:00-03:00", "action": "saida"},
        ])

        self.assertEqual(calculate_total_hours(df), "09:30")

    def test_generate_pdf_report_returns_pdf_bytes(self):
        df = pd.DataFrame([
            {"timestamp": "2024-01-01T08:00:00-03:00", "action": "entrada"},
            {"timestamp": "2024-01-01T17:30:00-03:00", "action": "saida"},
        ])

        pdf_bytes = generate_pdf_report("Maria", df, pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-01"))
        self.assertTrue(pdf_bytes)


if __name__ == "__main__":
    unittest.main()
