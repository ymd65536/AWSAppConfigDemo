import unittest

from app.step3_bedrock import build_detail_payload, summarize_text
from app.step4_bedrock import build_bedrock_request_body, extract_bedrock_text


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

    def test_build_bedrock_request_body_for_anthropic_model(self) -> None:
        body = build_bedrock_request_body(
            "anthropic.claude-3-haiku-20240307-v1:0",
            "Summarize this text.",
        )

        self.assertIn("anthropic_version", body)
        self.assertEqual(body["messages"][0]["role"], "user")

    def test_extract_bedrock_text_supports_anthropic_and_titan(self) -> None:
        anthropic_response = {"content": [{"type": "text", "text": "anthropic summary"}]}
        titan_response = {"results": [{"outputText": "titan summary"}]}

        self.assertEqual(extract_bedrock_text(anthropic_response), "anthropic summary")
        self.assertEqual(extract_bedrock_text(titan_response), "titan summary")


if __name__ == "__main__":
    unittest.main()
