from unittest.mock import Mock, patch
from app.main.views.activity import get_report_info


def test_report_metadata_loading_fix(mocker):
    """Test that metadata is loaded correctly after check_s3_file_exists"""
    mock_s3_obj = Mock()
    # After check_s3_file_exists calls load(), content_length is populated
    mock_s3_obj.content_length = 86528

    with patch('app.s3_client.get_s3_object', return_value=mock_s3_obj):
        with patch('app.s3_client.check_s3_file_exists', return_value=True):
            s3_config = {
                'bucket': 'test-bucket',
                'access_key_id': 'test-key',
                'secret_access_key': 'test-secret',  # pragma: allowlist secret
                'region': 'us-east-1'
            }

            result = get_report_info('service-123', '1-day-report', s3_config)

            assert result == {"available": True, "size": "84.5 KB"}


def test_report_not_found(mocker):
    """Test when report doesn't exist"""
    mock_s3_obj = Mock()

    with patch('app.s3_client.get_s3_object', return_value=mock_s3_obj):
        with patch('app.s3_client.check_s3_file_exists', return_value=False):
            s3_config = {
                'bucket': 'test-bucket',
                'access_key_id': 'test-key',
                'secret_access_key': 'test-secret',  # pragma: allowlist secret
                'region': 'us-east-1'
            }

            result = get_report_info('service-123', '1-day-report', s3_config)

            assert result == {"available": False, "size": None}
