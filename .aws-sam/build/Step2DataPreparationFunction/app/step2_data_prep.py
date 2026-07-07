import csv
import io
import logging
import os
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def build_sample_datasets() -> Dict[str, List[Dict[str, object]]]:
    customers = [
        {"customer_id": idx, "customer_name": f"Customer {idx}", "region": "ap-northeast-1"}
        for idx in range(1, 11)
    ]
    sales = [
        {
            "order_id": 1000 + idx,
            "customer_id": idx,
            "amount": 100 + idx,
            "order_date": f"2024-01-{idx:02d}",
        }
        for idx in range(1, 11)
    ]
    return {"customers": customers, "sales": sales}


def render_csv(rows: List[Dict[str, object]], columns: List[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _ensure_bucket(bucket_name: str) -> None:
    region = os.getenv("AWS_REGION", "ap-northeast-1")
    client = boto3.client("s3", region_name=region)
    try:
        client.head_bucket(Bucket=bucket_name)
        return
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in {"404", "403"}:
            raise

    create_bucket_kwargs: Dict[str, Any] = {"Bucket": bucket_name}
    if region != "us-east-1":
        create_bucket_kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
    client.create_bucket(**create_bucket_kwargs)


def _ensure_glue_catalog(database_name: str, bucket_name: str) -> None:
    region = os.getenv("AWS_REGION", "ap-northeast-1")
    glue = boto3.client("glue", region_name=region)
    try:
        glue.get_database(Name=database_name)
    except glue.exceptions.EntityNotFoundException:
        glue.create_database(
            DatabaseInput={
                "Name": database_name,
                "Description": "Demo database for AppConfig Step2",
            }
        )

    table_specs = {
        "customers": {
            "columns": [
                {"Name": "customer_id", "Type": "int"},
                {"Name": "customer_name", "Type": "string"},
                {"Name": "region", "Type": "string"},
            ],
            "location": f"s3://{bucket_name}/raw/customers.csv",
        },
        "sales": {
            "columns": [
                {"Name": "order_id", "Type": "int"},
                {"Name": "customer_id", "Type": "int"},
                {"Name": "amount", "Type": "int"},
                {"Name": "order_date", "Type": "string"},
            ],
            "location": f"s3://{bucket_name}/raw/sales.csv",
        },
    }

    for table_name, spec in table_specs.items():
        try:
            glue.get_table(DatabaseName=database_name, Name=table_name)
        except glue.exceptions.EntityNotFoundException:
            glue.create_table(
                DatabaseName=database_name,
                TableInput={
                    "Name": table_name,
                    "TableType": "EXTERNAL_TABLE",
                    "Parameters": {"classification": "csv", "skip.header.line.count": "1"},
                    "StorageDescriptor": {
                        "Columns": spec["columns"],
                        "Location": spec["location"],
                        "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
                        "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                        "SerdeInfo": {
                            "SerializationLibrary": "org.apache.hadoop.hive.serde2.OpenCSVSerde",
                            "Parameters": {
                                "separatorChar": ",",
                                "quoteChar": '"',
                                "escapeChar": "\\",
                            },
                        },
                    },
                },
            )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    bucket_name = os.getenv("S3_BUCKET_NAME")
    database_name = os.getenv("GLUE_DATABASE_NAME", "appconfig_demo")
    if not bucket_name:
        return {"statusCode": 400, "body": {"error": "S3_BUCKET_NAME is required"}}

    datasets = build_sample_datasets()
    _ensure_bucket(bucket_name)
    _ensure_glue_catalog(database_name, bucket_name)

    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-northeast-1"))
    uploads = []
    for table_name, rows in datasets.items():
        columns = list(rows[0].keys())
        data = render_csv([dict(row) for row in rows], columns)
        key = f"raw/{table_name}.csv"
        s3.put_object(Bucket=bucket_name, Key=key, Body=data.encode("utf-8"))
        uploads.append({"table": table_name, "key": key})

    return {
        "statusCode": 200,
        "body": {
            "bucket": bucket_name,
            "database": database_name,
            "uploads": uploads,
        },
    }
