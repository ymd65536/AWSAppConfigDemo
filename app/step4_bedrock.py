import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="Step4 Bedrock API")


@app.get('/openapi.json')
async def openapi_json() -> Dict[str, Any]:
    return app.openapi()


@app.get('/docs', include_in_schema=False)
async def docs_page() -> FileResponse:
    return FileResponse(Path(__file__).resolve().parent.parent / 'templates' / 'swagger.html')


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
    region = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "ap-northeast-1"

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


def get_bedrock_model_id() -> str:
    return os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")


def build_bedrock_request_body(model_id: str, text: str) -> Dict[str, Any]:
    prompt = f"Summarize the following text in one sentence:\n\n{text}"
    if "anthropic" in model_id:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 256,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        }

    if "titan" in model_id:
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 256,
                "stopSequences": [],
                "temperature": 0,
                "topP": 0.9,
            },
        }

    return {"inputText": prompt, "textGenerationConfig": {"maxTokenCount": 256}}


def extract_bedrock_text(response_body: Dict[str, Any]) -> str:
    if not isinstance(response_body, dict):
        return ""

    if "content" in response_body:
        for item in response_body.get("content", []):
            if isinstance(item, dict) and item.get("type") == "text":
                return item.get("text", "")

    if "results" in response_body:
        for item in response_body.get("results", []):
            if isinstance(item, dict):
                output_text = item.get("outputText")
                if output_text:
                    return output_text

    if "outputText" in response_body:
        return response_body.get("outputText", "")

    return ""


def invoke_bedrock_summarization(text: str, model_id: Optional[str] = None) -> str:
    model_id = model_id or get_bedrock_model_id()
    if not text:
        return ""

    request_body = build_bedrock_request_body(model_id, text)
    region = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "ap-northeast-1"

    try:
        client = boto3.client("bedrock-runtime", region_name=region)
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json",
        )
        response_body = response.get("body")
        if response_body is None:
            return summarize_text(text)

        if hasattr(response_body, "read"):
            payload = response_body.read()
        else:
            payload = response_body

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        if isinstance(payload, str):
            payload = json.loads(payload)

        response_text = extract_bedrock_text(payload)
        if response_text:
            return response_text
    except Exception:
        pass

    return summarize_text(text)


@app.post("/bedrock_summarize")
async def bedrock_summarize(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = payload.get("text", "")
    model_id = payload.get("model_id") or get_bedrock_model_id()
    return {"model_id": model_id, "summary": invoke_bedrock_summarization(text, model_id)}


@app.get("/bedrock_detail")
async def bedrock_detail() -> Dict[str, Any]:
    configuration = _get_configuration_from_appconfig_data_api()
    if configuration is None:
        return {"error": "AppConfig configuration not found"}

    payload = build_detail_payload(configuration)
    payload["model_id"] = get_bedrock_model_id()
    return payload


def run_server() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    run_server()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "This function is intended to run behind AWS Lambda Web Adapter"}),
    }
