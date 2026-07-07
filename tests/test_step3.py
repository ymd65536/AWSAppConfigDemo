import unittest

from app.step3_bedrock import build_detail_payload, summarize_text


class Step3Tests(unittest.TestCase):
    def test_summarize_text_creates_short_summary(self) -> None:
        summary = summarize_text("Sales data includes customers and orders. The team reviews the trend every week.")

        self.assertIn("Sales data", summary)
        self.assertLessEqual(len(summary.split()), 12)

    def test_build_detail_payload_lists_searchable_data(self) -> None:
        schema = [
            {
                "model_id": "sales_performance",
                "target_table": "sales_summary",
                "sample_queries": ["show sales by region"],
            }
        ]

        payload = build_detail_payload(schema)

        self.assertEqual(payload["searchable_data"][0]["target_table"], "sales_summary")
        self.assertEqual(payload["searchable_data"][0]["sample_queries"][0], "show sales by region")

    def test_build_detail_payload_accepts_searchable_data_object(self) -> None:
        schema = {
            "searchable_data": [
                {
                    "model_id": "sales_performance",
                    "target_table": "sales_summary",
                    "sample_queries": ["show sales by region"],
                    "description": "Sales summary data",
                }
            ]
        }

        payload = build_detail_payload(schema)

        self.assertEqual(payload["searchable_data"][0]["target_table"], "sales_summary")
        self.assertEqual(payload["searchable_data"][0]["description"], "Sales summary data")


if __name__ == "__main__":
    unittest.main()
