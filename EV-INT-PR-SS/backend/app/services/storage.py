"""S3 / MinIO object storage service."""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings

_s3_client = None


def get_s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION,
            config=Config(signature_version="s3v4"),
        )
    return _s3_client


async def upload_file(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload bytes to S3/MinIO. Returns the S3 key."""
    get_s3().put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    return key


async def delete_file(bucket: str, key: str) -> None:
    try:
        get_s3().delete_object(Bucket=bucket, Key=key)
    except ClientError:
        pass  # best-effort delete


def generate_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    """Generate a presigned GET URL valid for `expires_in` seconds."""
    return get_s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )
