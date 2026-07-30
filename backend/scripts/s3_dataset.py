"""Upload, download, or list configured Amazon S3 dataset areas.

Examples:
    python scripts/s3_dataset.py list raw
    python scripts/s3_dataset.py upload raw ./movies.csv
    python scripts/s3_dataset.py download serving movies.jsonl ./movies.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.aws.infrastructure import create_aws_clients
from app.aws.s3_storage import S3DatasetStorage
from app.core.config import settings


def configured_prefixes() -> dict[str, str]:
    return {
        "dataset": settings.s3.dataset_prefix,
        "raw": settings.s3.raw_prefix,
        "processed": settings.s3.processed_prefix,
        # Feature files share datasets/processed/ in the canonical bucket.
        "features": settings.s3.processed_prefix,
        "serving": settings.s3.serving_prefix,
        "training": settings.s3.training_prefix,
        "models": settings.s3.model_prefix,
        "outputs": settings.s3.output_prefix,
        "interactions": settings.s3.interaction_export_prefix,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("area", choices=configured_prefixes())

    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("area", choices=configured_prefixes())
    upload_parser.add_argument("source", type=Path)
    upload_parser.add_argument("--name")

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("area", choices=configured_prefixes())
    download_parser.add_argument("object_name")
    download_parser.add_argument("destination", type=Path)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    clients = create_aws_clients(settings)
    storage = S3DatasetStorage(
        client=clients.s3_client,
        bucket=settings.s3.bucket,
    )
    prefix = configured_prefixes()[arguments.area]

    if arguments.action == "list":
        count = 0
        total = 0
        for item in storage.list_objects(prefix=prefix):
            print(f"{item.size:>12}  {item.key}")
            count += 1
            total += item.size
        print(f"{count} object(s), {total} byte(s)")
        return 0

    if arguments.action == "upload":
        uri = storage.upload_file(
            local_path=arguments.source,
            prefix=prefix,
            object_name=arguments.name,
        )
        print(uri)
        return 0

    destination = storage.download_file(
        prefix=prefix,
        object_name=arguments.object_name,
        destination=arguments.destination,
    )
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
