import os
from unittest.mock import MagicMock, Mock, patch

import botocore.exceptions
import pytest

from app.s3_client import (
    AWS_CLIENT_CONFIG,
    get_s3_contents,
    get_s3_metadata,
    get_s3_object,
    set_s3_metadata,
)


class TestS3ClientCoverage:
    """Coverage tests for s3_client/__init__.py"""

    def test_aws_client_config(self):
        """Test AWS_CLIENT_CONFIG is properly configured"""
        assert AWS_CLIENT_CONFIG.s3 == {"addressing_style": "virtual"}
        assert AWS_CLIENT_CONFIG.use_fips_endpoint is True

    @patch("app.s3_client.Session")
    @patch.dict(os.environ, {"NOTIFY_ENVIRONMENT": "production"})
    def test_get_s3_object_production(self, mock_session):
        """Test get_s3_object in production environment"""
        mock_resource = Mock()
        mock_obj = Mock()
        mock_session.return_value.resource.return_value = mock_resource
        mock_resource.Object.return_value = mock_obj

        result = get_s3_object(
            "test-bucket", "test-file.txt", "access-key", "secret-key", "us-east-1"
        )

        mock_session.assert_called_once_with(
            aws_access_key_id="access-key",
            aws_secret_access_key="secret-key",
            region_name="us-east-1",
        )
        mock_session.return_value.resource.assert_called_once_with(
            "s3", config=AWS_CLIENT_CONFIG
        )
        mock_resource.Object.assert_called_once_with("test-bucket", "test-file.txt")
        assert result == mock_obj

    @patch("app.s3_client.Session")
    @patch.dict(os.environ, {"NOTIFY_ENVIRONMENT": "test"})
    def test_get_s3_object_test_env_with_mock(self, mock_session):
        """Test get_s3_object in test environment with proper mocking"""
        mock_resource = Mock()
        mock_obj = Mock()
        mock_bucket = MagicMock()
        mock_bucket.creation_date = MagicMock()

        mock_session.return_value.resource.return_value = mock_resource
        mock_resource.Object.return_value = mock_obj
        mock_resource.Bucket.return_value = mock_bucket

        result = get_s3_object(
            "test-bucket", "test-file.txt", "access-key", "secret-key", "us-east-1"
        )

        assert result == mock_obj

    @patch("app.s3_client.Session")
    @patch.dict(os.environ, {"NOTIFY_ENVIRONMENT": "test"})
    def test_get_s3_object_test_env_without_mock(self, mock_session):
        """Test get_s3_object in test environment without proper mocking"""
        mock_resource = Mock()
        mock_obj = Mock()
        mock_bucket = Mock()
        mock_bucket.creation_date = "2024-01-01"  # Not a MagicMock

        mock_session.return_value.resource.return_value = mock_resource
        mock_resource.Object.return_value = mock_obj
        mock_resource.Bucket.return_value = mock_bucket

        with pytest.raises(Exception, match="Test is not mocked") as exc_info:
            get_s3_object(
                "test-bucket", "test-file.txt", "access-key", "secret-key", "us-east-1"
            )

        assert "Test is not mocked" in str(exc_info.value)

    def test_get_s3_metadata_success(self):
        """Test get_s3_metadata success case"""
        mock_obj = Mock()
        mock_obj.get.return_value = {"Metadata": {"key1": "value1", "key2": "value2"}}

        result = get_s3_metadata(mock_obj)

        assert result == {"key1": "value1", "key2": "value2"}
        mock_obj.get.assert_called_once()

    @patch("app.s3_client.current_app")
    def test_get_s3_metadata_client_error(self, mock_app):
        """Test get_s3_metadata with ClientError"""
        mock_logger = Mock()
        mock_app.logger = mock_logger

        mock_obj = Mock()
        mock_obj.bucket_name = "test-bucket"
        mock_obj.key = "test-key"
        mock_obj.get.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "NoSuchKey"}}, "GetObject"
        )

        with pytest.raises(botocore.exceptions.ClientError):
            get_s3_metadata(mock_obj)

        mock_logger.error.assert_called_once_with(
            "Unable to download s3 file test-bucket/test-key"
        )

    def test_set_s3_metadata(self):
        """Test set_s3_metadata"""
        mock_obj = Mock()
        mock_obj.bucket_name = "test-bucket"
        mock_obj.key = "test-key"
        mock_obj.copy_from.return_value = {"CopyObjectResult": {"ETag": "abc123"}}

        result = set_s3_metadata(
            mock_obj, metadata1="value1", metadata2=123, metadata3=True
        )

        mock_obj.copy_from.assert_called_once_with(
            CopySource="test-bucket/test-key",
            ServerSideEncryption="AES256",
            Metadata={"metadata1": "value1", "metadata2": "123", "metadata3": "True"},
            MetadataDirective="REPLACE",
        )
        assert result == {"CopyObjectResult": {"ETag": "abc123"}}

    def test_get_s3_contents_success(self):
        """Test get_s3_contents success case"""
        mock_obj = Mock()
        mock_body = Mock()
        mock_body.read.return_value = b"Hello, World!"
        mock_obj.get.return_value = {"Body": mock_body}

        result = get_s3_contents(mock_obj)

        assert result == "Hello, World!"
        mock_obj.get.assert_called_once()
        mock_body.read.assert_called_once()

    @patch("app.s3_client.current_app")
    def test_get_s3_contents_client_error(self, mock_app):
        """Test get_s3_contents with ClientError"""
        mock_logger = Mock()
        mock_app.logger = mock_logger

        mock_obj = Mock()
        mock_obj.bucket_name = "test-bucket"
        mock_obj.key = "test-key"
        mock_obj.get.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "AccessDenied"}}, "GetObject"
        )

        with pytest.raises(botocore.exceptions.ClientError):
            get_s3_contents(mock_obj)

        mock_logger.error.assert_called_once_with(
            "Unable to download s3 file test-bucket/test-key"
        )
