import os
import time
from typing import Any, Dict, List, Optional

import boto3


def build_default_query(table_name: str, database_name: Optional[str] = None) -> str:
    database = database_name or os.getenv("GLUE_DATABASE_NAME", "default")
    return f"SELECT * FROM {database}.{table_name} LIMIT 5"


def normalize_query_results(columns: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    column_names = [column.get("Name", "") for column in columns]
    normalized_rows = []

    for row in rows:
        if isinstance(row, dict) and "Data" in row:
            values = row.get("Data", [])
        elif isinstance(row, list):
            values = row
        else:
            values = []

        normalized_rows.append(
            {
                name: _extract_value(value)
                for name, value in zip(column_names, values)
            }
        )
    return {"columns": column_names, "rows": normalized_rows}


def _extract_value(value: Optional[Dict[str, Any]]) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, dict):
        return value.get("VarCharValue") or value.get("LongValue") or value.get("DoubleValue")
    return value


def run_query(query: str, workgroup: Optional[str] = None) -> Dict[str, Any]:
    client = boto3.client("athena", region_name=os.getenv("AWS_REGION", "ap-northeast-1"))
    response = client.start_query_execution(
        QueryString=query,
        ResultConfiguration={"OutputLocation": os.getenv("ATHENA_OUTPUT_S3_URI", "s3://example-bucket/athena-results")},
        WorkGroup=workgroup or os.getenv("ATHENA_WORKGROUP", "primary"),
    )
    execution_id = response.get("QueryExecutionId")
    if not execution_id:
        raise RuntimeError("Athena query execution id was not returned")

    for _ in range(15):
        execution = client.get_query_execution(QueryExecutionId=execution_id)
        state = execution["QueryExecution"]["Status"]["State"]
        if state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            break
        time.sleep(1)

    if execution["QueryExecution"]["Status"]["State"] != "SUCCEEDED":
        raise RuntimeError(execution["QueryExecution"]["Status"].get("StateChangeReason", "Athena query failed"))

    results = client.get_query_results(QueryExecutionId=execution_id)
    result_set = results.get("ResultSet", {})
    column_info = result_set.get("ResultSetMetadata", {}).get("ColumnInfo", [])
    rows = result_set.get("Rows", [])[1:]
    return {
        "queryExecutionId": execution_id,
        "result": normalize_query_results(column_info, rows),
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    table_name = event.get("table_name", "customers")
    database_name = event.get("database_name") or os.getenv("GLUE_DATABASE_NAME", "appconfig_demo")
    query = event.get("query") or build_default_query(table_name, database_name)
    result = run_query(query)
    return {"statusCode": 200, "body": {"query": query, "result": result}}
