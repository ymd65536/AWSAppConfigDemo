import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional

PORT = int(os.getenv("AWS_APPCONFIG_EXTENSION_HTTP_PORT", "2772"))
APPLICATION_ID = os.getenv("AWS_APPCONFIG_APPLICATION_ID")
ENVIRONMENT_ID = os.getenv("AWS_APPCONFIG_ENVIRONMENT_ID")
PROFILE_ID = os.getenv("AWS_APPCONFIG_CONFIGURATION_PROFILE_ID")


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

        url = (
            "https://appconfig.ap-northeast-1.amazonaws.com/applications/"
            f"{APPLICATION_ID}/environments/{ENVIRONMENT_ID}/configurations/{PROFILE_ID}"
        )
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
            return {
                "message": "AppConfig extension fallback",
                "feature_enabled": False,
                "source": "extension-fallback",
            }


def serve() -> None:
    server = HTTPServer(("127.0.0.1", PORT), AppConfigHandler)
    server.serve_forever()


if __name__ == "__main__":
    serve()
