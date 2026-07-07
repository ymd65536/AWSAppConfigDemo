import io
import json
import os
import unittest
from unittest.mock import patch

from app.app import _get_configuration_from_appconfig_data_api, lambda_handler, load_configuration


class AppConfigLambdaTests(unittest.TestCase):
    def test_load_configuration_from_extension(self) -> None:
        with patch("app.app.boto3.client") as mock_client:
            mock_client.return_value.start_configuration_session.return_value = {
                "InitialConfigurationToken": "token"
            }
            mock_client.return_value.get_latest_configuration.return_value = {
                "Configuration": io.BytesIO(b'{"message": "from-extension", "feature_enabled": true}')
            }

            with patch.dict(
                os.environ,
                {
                    "AWS_APPCONFIG_APPLICATION_ID": "app-id",
                    "AWS_APPCONFIG_ENVIRONMENT_ID": "env-id",
                    "AWS_APPCONFIG_CONFIGURATION_PROFILE_ID": "profile-id",
                },
                clear=True,
            ):
                configuration = load_configuration()

        self.assertEqual(configuration["message"], "from-extension")
        self.assertTrue(configuration["feature_enabled"])

    def test_falls_back_to_default_configuration_when_appconfig_is_unavailable(self) -> None:
        with patch("app.app.urllib.request.urlopen", side_effect=Exception("not available")):
            with patch.dict(os.environ, {}, clear=True):
                configuration = load_configuration()

        self.assertEqual(configuration["source"], "fallback")
        self.assertFalse(configuration["feature_enabled"])

    def test_get_configuration_from_appconfig_data_api(self) -> None:
        with patch("app.app.boto3.client") as mock_client:
            mock_client.return_value.start_configuration_session.return_value = {
                "InitialConfigurationToken": "token"
            }
            mock_client.return_value.get_latest_configuration.return_value = {
                "Configuration": io.BytesIO(b'{"message": "from-api", "feature_enabled": true}')
            }

            with patch.dict(
                os.environ,
                {
                    "AWS_APPCONFIG_APPLICATION_ID": "app-id",
                    "AWS_APPCONFIG_ENVIRONMENT_ID": "env-id",
                    "AWS_APPCONFIG_CONFIGURATION_PROFILE_ID": "profile-id",
                },
                clear=True,
            ):
                configuration = _get_configuration_from_appconfig_data_api()

        self.assertEqual(configuration["message"], "from-api")
        self.assertTrue(configuration["feature_enabled"])

    def test_lambda_handler_returns_status_and_body(self) -> None:
        with patch("app.app.load_configuration", return_value={"message": "ok"}):
            result = lambda_handler({}, None)

        self.assertEqual(result["statusCode"], 200)
        payload = json.loads(result["body"])
        self.assertEqual(payload["configuration"]["message"], "ok")


if __name__ == "__main__":
    unittest.main()
