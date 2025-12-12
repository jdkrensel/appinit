"""Lambda function for handling binary download requests.

This function handles GET requests to the /download endpoint and provides
presigned URLs for downloading AppInit binaries from S3. It supports automatic
platform and architecture detection from query parameters or User-Agent headers.

Environment Variables:
    BUCKET_NAME: Name of the S3 bucket containing the binaries

Query Parameters:
    platform: Target platform (linux, darwin, windows)
    arch: Target architecture (amd64, arm64)

Returns:
    302 redirect to presigned S3 URL for binary download
    404 if binary not found for the requested platform/architecture
"""

import json
import os
from typing import Any, Literal, TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client


s3_client: "S3Client" = boto3.client("s3")  # Module-level client for Lambda warm container reuse


def _detect_platform_from_user_agent(user_agent: str) -> str:
    """Detect platform from User-Agent header."""
    user_agent = user_agent.lower()

    platforms: dict[str, tuple[str, ...]] = {
        "darwin": ("darwin", "mac"),
        "windows": ("windows", "win"),
    }

    for platform, keywords in platforms.items():
        if any(keyword in user_agent for keyword in keywords):
            return platform

    return "linux"


def _detect_arch_from_user_agent(user_agent: str) -> str:
    """Detect architecture from User-Agent header."""
    user_agent = user_agent.lower()

    architectures: dict[str, tuple[str, ...]] = {
        "arm64": ("arm64", "aarch64"),
    }

    for arch, keywords in architectures.items():
        if any(keyword in user_agent for keyword in keywords):
            return arch

    return "amd64"


def _get_platform_and_arch(event: dict[str, Any]) -> tuple[str, str]:
    """Extract or detect platform and architecture from request."""
    query_params = event.get("queryStringParameters", {})
    platform = query_params.get("platform", "")
    arch = query_params.get("arch", "")

    if not platform or not arch:
        user_agent = event.get("headers", {}).get("User-Agent", "")
        if not platform:
            platform: str = _detect_platform_from_user_agent(user_agent)
        if not arch:
            arch: str = _detect_arch_from_user_agent(user_agent)

    return platform, arch


def _construct_binary_key(platform: str, arch: str) -> str:
    """Construct S3 key for binary based on platform and architecture."""
    suffix: Literal[".exe", ""] = ".exe" if platform == "windows" else ""
    return f"appinit-{platform}-{arch}{suffix}"


def lambda_handler(
    event: dict[str, Any],
    _context: Any,
) -> dict[str, Any]:
    """Handle binary download requests with platform detection.

    Args:
        event: API Gateway event containing request details including query parameters
               and headers for platform/architecture detection
        _context: Lambda context object (unused)

    Returns:
        HTTP response with 302 redirect to presigned S3 URL for binary download,
        or 404 if binary not found for the requested platform/architecture
    """
    bucket_name = os.environ["BUCKET_NAME"]
    presigned_url_expiry = int(os.environ.get("PRESIGNED_URL_EXPIRY", "3600"))

    platform, arch = _get_platform_and_arch(event)
    binary_key = _construct_binary_key(platform, arch)

    try:
        download_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": binary_key},
            ExpiresIn=presigned_url_expiry,
        )

        return {
            "statusCode": 302,
            "headers": {
                "Location": download_url,
                "Content-Type": "application/octet-stream",
                "Content-Disposition": f'attachment; filename="{binary_key}"',
            },
        }
    except (ClientError, Exception):
        return {
            "statusCode": 404,
            "body": json.dumps(
                {
                    "error": f"Binary not found for {platform}/{arch}",
                    "available_binaries": "Check /list endpoint",
                }
            ),
        }
