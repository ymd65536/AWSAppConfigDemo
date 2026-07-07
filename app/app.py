import json
import logging
import os
import boto3
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
    except Exception as exc:
        logger.exception("Failed to load AppConfig configuration: %s", exc)
        return None

    return None


def load_configuration() -> Dict[str, Any]:
    configured = _get_configuration_from_appconfig_data_api()
    if configured is not None:
        return configured

    return {
        "message": "AppConfig is not available; using fallback configuration.",
        "feature_enabled": False,
        "source": "fallback",
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    configuration = load_configuration()
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Configuration retrieved successfully",
                "configuration": configuration,
            }
        ),
    }
