import uuid
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import get_settings

settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
    "image/png": "png",
}

_s3_region_cache: str | None = None


def _discover_bucket_region() -> str:
    """
    Discover the real bucket region. Start with the configured aws_region and
    verify it via head_bucket. If a redirect is returned, use that region instead.
    """
    global _s3_region_cache
    if _s3_region_cache:
        return _s3_region_cache

    configured_region = settings.aws_region  # e.g. ap-south-1
    try:
        probe = boto3.client(
            "s3",
            region_name=configured_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
            config=Config(signature_version="s3v4"),
        )
        probe.head_bucket(Bucket=settings.s3_bucket_name)
        # head_bucket succeeded with configured region — use it
        _s3_region_cache = configured_region
    except ClientError as e:
        # Extract actual bucket region from redirect header
        bucket_region = e.response.get("ResponseMetadata", {}).get(
            "HTTPHeaders", {}
        ).get("x-amz-bucket-region")
        _s3_region_cache = bucket_region or configured_region
    except Exception:
        _s3_region_cache = configured_region

    return _s3_region_cache


def _get_s3_client():
    region = _discover_bucket_region()
    return boto3.client(
        "s3",
        region_name=region,
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


def upload_to_s3(s3_key: str, file_content: bytes, content_type: str) -> None:
    """Upload file bytes directly to S3."""
    client = _get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=s3_key,
        Body=file_content,
        ContentType=content_type,
    )


def get_s3_object_bytes(s3_key: str) -> bytes:
    client = _get_s3_client()
    response = client.get_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    return response["Body"].read()
