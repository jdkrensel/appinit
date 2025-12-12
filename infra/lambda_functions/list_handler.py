"""Lambda function for listing available binaries.

This function handles GET requests to the /list endpoint and returns a JSON
response containing all available binaries in the S3 bucket with their
metadata (size, last modified date).

Environment Variables:
    BUCKET_NAME: Name of the S3 bucket containing the binaries

Returns:
    JSON response with list of available binaries and download URL template
"""

import json
import os
from typing import Any, TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import ListObjectsV2OutputTypeDef, ObjectTypeDef


s3_client: "S3Client" = boto3.client("s3")  # Module-level client for Lambda warm container reuse


def _format_binary_info(obj: "ObjectTypeDef") -> dict[str, Any]:
    """Format S3 object information for API response."""
    last_modified = obj.get("LastModified")
    return {
        "name": obj.get("Key", ""),
        "size": obj.get("Size", 0),
        "last_modified": last_modified.isoformat() if last_modified else "",
    }


def _get_binaries_from_s3() -> list[dict[str, Any]]:
    """Retrieve and format binary information from S3 bucket."""
    bucket_name = os.environ["BUCKET_NAME"]
    response: "ListObjectsV2OutputTypeDef" = s3_client.list_objects_v2(Bucket=bucket_name)
    binaries: list[dict[str, Any]] = []

    if "Contents" in response:
        for obj in response["Contents"]:
            binaries.append(_format_binary_info(obj))

    return binaries


def lambda_handler(
    _event: dict[str, Any],
    _context: Any,
) -> dict[str, Any]:
    """List all available binaries in the S3 bucket.

    Args:
        _event: API Gateway event containing request details (unused)
        _context: Lambda context object (unused)

    Returns:
        HTTP response with JSON list of available binaries including metadata
        (name, size, last modified date) and download URL template
    """
    try:
        binaries = _get_binaries_from_s3()

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "binaries": binaries,
                    "download_url": "https://your-api-url/download?platform=<platform>&arch=<arch>",
                }
            ),
        }
    except (ClientError, Exception) as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
