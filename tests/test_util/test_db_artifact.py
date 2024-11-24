import unittest
from botocore.exceptions import ClientError
from unittest.mock import patch
from util.common_utils import get_logger
from util.db_artifact import S3Client

logger = get_logger("tests.test_util.test_db_artifact")

class TestS3Client(unittest.TestCase):
    def setUp(self) -> None:
        self.bucket = "test-cicd-cs6510"
        self.ok_error = ClientError(
            error_response={
                'Error':{
                    'Code':'BucketAlreadyOwnedByYou'
                }
            },
            operation_name='create_bucket'
        )

    @patch("util.db_artifact.boto3.client")
    def test_constructor(self, mock_s3):
        """ Test error handling of the constructor

        Args:
            mock_s3 (MagicMock): mock s3 creation
        """
        mock_s3_client = mock_s3.return_value
        # mock the create_bucket method of mock_s3_client,
        # when Error Code is 'BucketAlreadyOwnedByYou', this should be caught
        mock_s3_client.create_bucket.side_effect = self.ok_error
        s3_client = S3Client(self.bucket)
        assert True
        # when Error Code is others, this should be raised
        mock_s3_client.create_bucket.side_effect = ClientError(
            error_response={
                'Error':{
                    'Code':'random'
                }
            },
            operation_name='create_bucket'
        )
        try:
            s3_client = S3Client(self.bucket)
            assert False
        except ClientError:
            assert True

    @patch("util.db_artifact.os.path.basename", return_value="file")
    @patch("util.db_artifact.boto3.client")
    def test_upload_fail(self, mock_s3, mock_basename):
        """ Test error handling of the upload_file method

        Args:
            mock_s3 (MagicMock): mock s3 creation
        """
        mock_s3_client = mock_s3.return_value
        # mock the create_bucket method of mock_s3_client, 
        # when Error Code is 'BucketAlreadyOwnedByYou', this should be caught
        mock_s3_client.create_bucket.side_effect = self.ok_error
        s3_client = S3Client(self.bucket)

        # Check if TypeError is correctly handled
        mock_s3_client.upload_file.side_effect = TypeError()
        response = s3_client.upload_file("file")
        assert response == False

        # Check if ClientError is correctly handled
        mock_s3_client.upload_file.side_effect = self.ok_error
        response = s3_client.upload_file("file")
        assert response == False
