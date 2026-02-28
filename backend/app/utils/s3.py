import uuid
import boto3
from botocore.config import Config

from app.config import get_settings

settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
    "image/png": "png",
}


def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
        config=Config(signature_version="s3v4"),
    )


def generate_presigned_upload_url(
    tenant_id: str, file_name: str, content_type: str
) -> tuple[str, str]:
    """Generate a presigned PUT URL for direct upload to S3.

    Returns (presigned_url, s3_key).
    """
    ext = ALLOWED_CONTENT_TYPES.get(content_type, "bin")
    s3_key = f"tenants/{tenant_id}/documents/{uuid.uuid4()}.{ext}"

    client = _get_s3_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket_name,
            "Key": s3_key,
            "ContentType": content_type,
        },
        ExpiresIn=3600,
    )
    return url, s3_key


def generate_presigned_download_url(s3_key: str, expiration: int = 3600) -> str:
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": s3_key},
        ExpiresIn=expiration,
    )


def get_s3_object_bytes(s3_key: str) -> bytes:
    client = _get_s3_client()
    response = client.get_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    return response["Body"].read()
