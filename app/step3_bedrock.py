import json
import os
from typing import Any, Dict, Optional

import boto3
from fastapi import FastAPI

from app.step4_bedrock import build_detail_payload, summarize_text

app = FastAPI(title="Step3 Bedrock API")


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
