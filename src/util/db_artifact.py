""" Module to manage upload files to aws s3
"""
import os
import boto3
from botocore.exceptions import ClientError
from util.common_utils import (get_env, get_logger)

DEFAULT_S3_LOC = 'us-west-2'
env = get_env()
logger = get_logger("util.db_artifact")
# pylint: disable=logging-fstring-interpolation
# pylint: disable=too-few-public-methods
class S3Client:
    """ Class to handle operations related to artifacts upload to s3
    """

    def __init__(self, bucket_name:str) -> None:
        """ initialize the object based on given bucket_name

        Args:
            bucket_name (str): target bucket to store the artifact

        Raises:
            ClientError: error in initializing s3 client
        """
        try:
            self.bucket_name = bucket_name
            s3_region = DEFAULT_S3_LOC
            if "AWS_S3_REGION" in env:
                s3_region = env["AWS_S3_REGION"]
            self.s3_client = boto3.client('s3')
            self.s3_client.create_bucket(
                CreateBucketConfiguration={
                    'LocationConstraint': s3_region,
                },
                Bucket=bucket_name,
            )
        except ClientError as ce:
            error_code = ce.response['Error']['Code']
            # raise if the error_code not related to 'BucketAlreadyOwnedByYou'
            if error_code != 'BucketAlreadyOwnedByYou':
                logger.warning(f"Error in initializing s3client, error is {ce.response}")
                raise ce

    def upload_file(self, file_name:str) -> bool:
        """ Upload a file to target s3 bucket

        Args:
            file_name (str): file name to upload

        Returns:
            bool: True if file was uploaded, else False
        """
        try:
            object_name = os.path.basename(file_name)
            self.s3_client.upload_file(file_name, self.bucket_name, object_name)
            return True
        except (TypeError, ClientError) as e:
            error_msg = f"Error in uploading file for {file_name}\n"
            error_msg += f"Error message = {str(e)}"
            logger.warning(error_msg)
            return False
