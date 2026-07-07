import csv
import io
import unittest

from app.step2_data_prep import build_sample_datasets, render_csv
from app.step2_athena import build_default_query, normalize_query_results


class Step2Tests(unittest.TestCase):
    def test_build_sample_datasets_create_ten_rows_each(self) -> None:
        datasets = build_sample_datasets()

        self.assertEqual(len(datasets["customers"]), 10)
        self.assertEqual(len(datasets["sales"]), 10)
        self.assertEqual(datasets["customers"][0]["customer_id"], 1)
        self.assertEqual(datasets["sales"][0]["order_id"], 1001)

    def test_render_csv_includes_header_and_rows(self) -> None:
        rows = [{"customer_id": 1, "customer_name": "Alice"}]
        csv_text = render_csv(rows, ["customer_id", "customer_name"])

        self.assertIn("customer_id,customer_name", csv_text)
        self.assertIn("1,Alice", csv_text)

    def test_build_default_query_uses_database_and_table_name(self) -> None:
        query = build_default_query("demo_customers", "demo_db")

        self.assertEqual(query, "SELECT * FROM demo_db.demo_customers LIMIT 5")

    def test_normalize_query_results_flattens_rows(self) -> None:
        columns = [{"Name": "customer_id"}, {"Name": "customer_name"}]
        rows = [{"Data": [{"VarCharValue": "1"}, {"VarCharValue": "Alice"}]}]

        normalized = normalize_query_results(columns, rows)

        self.assertEqual(normalized["columns"], ["customer_id", "customer_name"])
        self.assertEqual(normalized["rows"][0]["customer_id"], "1")
        self.assertEqual(normalized["rows"][0]["customer_name"], "Alice")


if __name__ == "__main__":
    unittest.main()
