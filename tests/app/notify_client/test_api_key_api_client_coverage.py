from unittest.mock import patch

from app.enums import ApiKeyType
from app.notify_client.api_key_api_client import (
    KEY_TYPE_NORMAL,
    KEY_TYPE_TEAM,
    KEY_TYPE_TEST,
    ApiKeyApiClient,
)


class TestApiKeyApiClientCoverage:
    """Coverage tests for api_key_api_client.py"""

    def test_key_type_constants(self):
        """Test that key type constants are properly set"""
        assert KEY_TYPE_NORMAL == ApiKeyType.NORMAL
        assert KEY_TYPE_TEAM == ApiKeyType.TEAM
        assert KEY_TYPE_TEST == ApiKeyType.TEST

    @patch("app.notify_client.api_key_api_client._attach_current_user")
    def test_get_api_keys(self, mock_attach_user, mocker):
        """Test get_api_keys method"""
        client = ApiKeyApiClient()
        mock_get = mocker.patch.object(client, "get", return_value={"keys": []})

        result = client.get_api_keys("service-123")

        mock_get.assert_called_once_with(url="/service/service-123/api-keys")
        assert result == {"keys": []}

    @patch("app.notify_client.api_key_api_client._attach_current_user")
    def test_create_api_key(self, mock_attach_user, mocker):
        """Test create_api_key method"""
        client = ApiKeyApiClient()
        mock_attach_user.return_value = {
            "name": "Test Key",
            "key_type": "normal",
            "created_by": "user-123",
        }
        mock_post = mocker.patch.object(
            client, "post", return_value={"data": {"id": "key-123", "name": "Test Key"}}
        )

        result = client.create_api_key("service-123", "Test Key", "normal")

        mock_attach_user.assert_called_once_with(
            {"name": "Test Key", "key_type": "normal"}
        )
        mock_post.assert_called_once_with(
            url="/service/service-123/api-key",
            data={"name": "Test Key", "key_type": "normal", "created_by": "user-123"},
        )
        assert result == {"id": "key-123", "name": "Test Key"}

    @patch("app.notify_client.api_key_api_client._attach_current_user")
    def test_revoke_api_key(self, mock_attach_user, mocker):
        """Test revoke_api_key method"""
        client = ApiKeyApiClient()
        mock_attach_user.return_value = {"created_by": "user-123"}
        mock_post = mocker.patch.object(client, "post", return_value={"success": True})

        result = client.revoke_api_key("service-123", "key-456")

        mock_attach_user.assert_called_once_with({})
        mock_post.assert_called_once_with(
            url="/service/service-123/api-key/revoke/key-456",
            data={"created_by": "user-123"},
        )
        assert result == {"success": True}

    def test_api_key_api_client_singleton(self):
        """Test that api_key_api_client is created"""
        from app.notify_client.api_key_api_client import api_key_api_client

        assert api_key_api_client is not None
        assert isinstance(api_key_api_client, ApiKeyApiClient)
