import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict

import boto3

PORT = int(os.getenv("AWS_APPCONFIG_EXTENSION_HTTP_PORT", "2772"))
APPLICATION_ID = os.getenv("AWS_APPCONFIG_APPLICATION_ID")
ENVIRONMENT_ID = os.getenv("AWS_APPCONFIG_ENVIRONMENT_ID")
PROFILE_ID = os.getenv("AWS_APPCONFIG_CONFIGURATION_PROFILE_ID")
REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "ap-northeast-1"


class AppConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/applications/"):
            payload = self._load_configuration()
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _load_configuration(self) -> Dict[str, Any]:
        if not all([APPLICATION_ID, ENVIRONMENT_ID, PROFILE_ID]):
            return {
                "message": "AppConfig environment variables are not set",
                "feature_enabled": False,
                "source": "extension-fallback",
            }

        try:
            client = boto3.client("appconfigdata", region_name=REGION)
            session = client.start_configuration_session(
                ApplicationIdentifier=APPLICATION_ID,
                EnvironmentIdentifier=ENVIRONMENT_ID,
                ConfigurationProfileIdentifier=PROFILE_ID,
            )
            token = session.get("InitialConfigurationToken")
            if not token:
                raise RuntimeError("No initial configuration token returned")

            response = client.get_latest_configuration(ConfigurationToken=token)
            payload = response.get("Configuration")
            if payload:
                return json.loads(payload.decode("utf-8"))
        except Exception:
            return {
                "message": "AppConfig extension fallback",
                "feature_enabled": False,
                "source": "extension-fallback",
            }

        return {
            "message": "AppConfig extension returned no configuration",
            "feature_enabled": False,
            "source": "extension-fallback",
        }


def serve() -> None:
    server = HTTPServer(("127.0.0.1", PORT), AppConfigHandler)
    server.serve_forever()


if __name__ == "__main__":
    serve()
