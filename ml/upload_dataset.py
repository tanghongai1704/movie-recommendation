#!/usr/bin/env python3
"""Upload a local dataset directory to an S3 bucket.

This script scans a local data folder, uploads each file to a target prefix in
Amazon S3, skips files that already exist, and prints a summary of the outcome.
It uses boto3 with AWS CLI credentials, pathlib for path handling, and logging
for structured output.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

# Configure logging so the script produces clear output and can be reused in
# production environments.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_s3_client() -> boto3.client:
    """Create a boto3 S3 client using AWS CLI credentials.

    The AWS SDK automatically resolves credentials from the standard AWS CLI
    configuration chain, including shared credentials and profile settings.
    """
    return boto3.client("s3")


def bucket_exists(s3_client: boto3.client, bucket_name: str) -> bool:
    """Check whether the target bucket already exists in S3.

    Args:
        s3_client: Configured boto3 S3 client.
        bucket_name: Name of the S3 bucket to verify.

    Returns:
        True if the bucket exists; otherwise False.
    """
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as exc:
        # A 404 indicates the bucket does not exist, while other ClientError
        # responses may indicate permission issues.
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchBucket"}:
            return False
        raise


def object_exists(s3_client: boto3.client, bucket_name: str, object_key: str) -> bool:
    """Check whether an object already exists in S3.

    Args:
        s3_client: Configured boto3 S3 client.
        bucket_name: S3 bucket name.
        object_key: Destination key inside the bucket.

    Returns:
        True if the object exists; otherwise False.
    """
    try:
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NotFound"}:
            return False
        raise


def upload_file(
    s3_client: boto3.client,
    bucket_name: str,
    source_file: Path,
    destination_prefix: str = "raw-data",
) -> Tuple[bool, str]:
    """Upload a single file to S3 if it does not already exist.

    Args:
        s3_client: Configured boto3 S3 client.
        bucket_name: Destination S3 bucket.
        source_file: Local file that should be uploaded.
        destination_prefix: Prefix inside the bucket.

    Returns:
        A tuple containing a boolean indicating success and a status message.
    """
    object_key = f"{destination_prefix}/{source_file.name}"

    try:
        if object_exists(s3_client, bucket_name, object_key):
            return False, f"[SKIP] {source_file.name} already exists."

        s3_client.upload_file(str(source_file), bucket_name, object_key)
        return True, f"[UPLOAD] {source_file.name} uploaded successfully."
    except FileNotFoundError as exc:
        logger.exception("Local file not found: %s", source_file)
        return False, f"[FAILED] {source_file.name} - FileNotFoundError: {exc}"
    except NoCredentialsError as exc:
        logger.exception("AWS credentials are missing")
        return False, f"[FAILED] {source_file.name} - NoCredentialsError: {exc}"
    except PartialCredentialsError as exc:
        logger.exception("AWS credentials are incomplete")
        return False, f"[FAILED] {source_file.name} - PartialCredentialsError: {exc}"
    except ClientError as exc:
        logger.exception("S3 client error while uploading %s", source_file.name)
        return False, f"[FAILED] {source_file.name} - ClientError: {exc}"
    except Exception as exc:  # pragma: no cover - broad fallback for unexpected errors.
        logger.exception("Unexpected error while uploading %s", source_file.name)
        return False, f"[FAILED] {source_file.name} - Unexpected Exception: {exc}"


def upload_directory(
    data_directory: Path,
    bucket_name: str,
    destination_prefix: str = "raw-data",
) -> Dict[str, List[str]]:
    """Upload every file in a local directory to S3.

    Args:
        data_directory: Directory containing the local dataset files.
        bucket_name: Target S3 bucket.
        destination_prefix: Prefix under which each file is stored.

    Returns:
        A dictionary with keys: uploaded, skipped, failed.
    """
    s3_client = create_s3_client()

    if not data_directory.exists():
        raise FileNotFoundError(f"Data directory not found: {data_directory}")

    if not data_directory.is_dir():
        raise NotADirectoryError(f"Data path is not a directory: {data_directory}")

    if not bucket_exists(s3_client, bucket_name):
        raise ValueError(f"S3 bucket does not exist: {bucket_name}")

    summary: Dict[str, List[str]] = {"uploaded": [], "skipped": [], "failed": []}

    for file_path in sorted(data_directory.iterdir()):
        if not file_path.is_file():
            continue

        success, message = upload_file(s3_client, bucket_name, file_path, destination_prefix)
        logger.info(message)

        if message.startswith("[UPLOAD]"):
            summary["uploaded"].append(file_path.name)
        elif message.startswith("[SKIP]"):
            summary["skipped"].append(file_path.name)
        elif message.startswith("[FAILED]"):
            summary["failed"].append(file_path.name)

    return summary


def print_summary(summary: Dict[str, List[str]]) -> None:
    """Print a final summary table for the upload run."""
    logger.info("\nSummary:")
    logger.info("Uploaded:")
    for item in summary["uploaded"]:
        logger.info(f"- {item}")

    logger.info("Skipped:")
    for item in summary["skipped"]:
        logger.info(f"- {item}")

    logger.info("Failed:")
    for item in summary["failed"]:
        logger.info(f"- {item}")


def main() -> None:
    """Run the dataset upload process."""
    bucket_name = "movie-recommend-demo-fcaj"
    data_directory = Path(__file__).resolve().parent / "data"
    destination_prefix = "raw-data"

    logger.info("Starting dataset upload process...")
    logger.info("Bucket: %s", bucket_name)
    logger.info("Source directory: %s", data_directory)
    logger.info("Destination prefix: %s", destination_prefix)

    try:
        summary = upload_directory(data_directory, bucket_name, destination_prefix)
    except FileNotFoundError as exc:
        logger.exception("Data directory issue: %s", exc)
        return
    except NotADirectoryError as exc:
        logger.exception("Data path issue: %s", exc)
        return
    except ValueError as exc:
        logger.exception("Bucket configuration issue: %s", exc)
        return
    except NoCredentialsError as exc:
        logger.exception("AWS credentials not found: %s", exc)
        return
    except PartialCredentialsError as exc:
        logger.exception("AWS credentials incomplete: %s", exc)
        return
    except ClientError as exc:
        logger.exception("S3 client error during upload: %s", exc)
        return
    except Exception as exc:  # pragma: no cover - broad fallback for unexpected errors.
        logger.exception("Unexpected error during upload: %s", exc)
        return

    print_summary(summary)
    logger.info("Dataset upload process completed.")


if __name__ == "__main__":
    main()
