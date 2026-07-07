import json
import os
import re
from typing import Any, Dict, List, Optional

import boto3
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI(title="Step3 Bedrock API")


def summarize_text(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""

    first_sentence = re.split(r"(?<=[.!?])\s+", cleaned)[0]
    words = first_sentence.split()
    if len(words) > 10:
        return " ".join(words[:10])
    return first_sentence


def build_detail_payload(schema: List[Dict[str, Any]] | Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(schema, dict) and "searchable_data" in schema:
        items = schema.get("searchable_data", [])
    else:
        items = schema

    searchable_data = []
    for item in items:
        if isinstance(item, dict):
            searchable_data.append(
                {
                    "model_id": item.get("model_id"),
                    "target_table": item.get("target_table"),
                    "sample_queries": item.get("sample_queries", []),
                    "description": item.get("description"),
                }
            )
    return {"searchable_data": searchable_data}


def _get_configuration_from_appconfig_data_api() -> Optional[Dict[str, Any]]:
    application_id = os.getenv("AWS_APPCONFIG_APPLICATION_ID")
    environment_id = os.getenv("AWS_APPCONFIG_ENVIRONMENT_ID")
    configuration_profile_id = os.getenv("AWS_APPCONFIG_CONFIGURATION_PROFILE_ID")
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "ap-northeast-1"

    if not all([application_id, environment_id, configuration_profile_id]):
        return None

    try:
        client = boto3.client("appconfigdata", region_name=region)
        session = client.start_configuration_session(
            ApplicationIdentifier=application_id,
            EnvironmentIdentifier=environment_id,
            ConfigurationProfileIdentifier=configuration_profile_id,
        )
        token = session.get("InitialConfigurationToken")
        if not token:
            return None

        response = client.get_latest_configuration(ConfigurationToken=token)
        payload = response.get("Configuration")
        if payload:
            if hasattr(payload, "read"):
                payload = payload.read()
            if isinstance(payload, bytes):
                return json.loads(payload.decode("utf-8"))
            if isinstance(payload, str):
                return json.loads(payload)
    except Exception:
        return None
    return None


@app.post("/summarize")
async def summarize(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = payload.get("text", "")
    return {"summary": summarize_text(text)}


@app.get("/detail")
async def detail() -> Dict[str, Any]:
    configuration = _get_configuration_from_appconfig_data_api()
    if configuration is None:
        return {"error": "AppConfig configuration not found"}
    return build_detail_payload(configuration)


handler = Mangum(app, lifespan="off")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    return handler(event, context)
