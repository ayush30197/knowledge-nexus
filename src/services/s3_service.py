from botocore.exceptions import ClientError
import boto3

from src.config.settings import get_settings
from src.utils.logger import logger


class S3Service:

    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )

    def upload_document(
        self,
        file,
        object_name: str,
    ):
        try:
            self.client.upload_fileobj(
                Fileobj=file,
                Bucket=self.bucket,
                Key=object_name,
            )

            logger.info(
                "Successfully uploaded object '%s' to bucket '%s'",
                object_name,
                self.bucket,
            )

        except ClientError:
            logger.error(
                "Failed uploading object '%s' to bucket '%s'",
                object_name,
                self.bucket,
            )
            raise