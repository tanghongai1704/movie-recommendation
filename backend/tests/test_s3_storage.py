import tempfile
import unittest
from pathlib import Path
from typing import Any

from app.aws.s3_storage import S3DatasetStorage


class FakeS3Client:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str]] = []
        self.downloads: list[tuple[str, str, str]] = []

    def upload_file(self, source: str, bucket: str, key: str) -> None:
        self.uploads.append((source, bucket, key))

    def download_file(self, bucket: str, key: str, destination: str) -> None:
        self.downloads.append((bucket, key, destination))

    def list_objects_v2(self, **options: Any) -> dict[str, Any]:
        del options
        return {
            "Contents": [
                {"Key": "data/raw/movies.csv", "Size": 100, "ETag": "etag"}
            ]
        }


class S3DatasetStorageTests(unittest.TestCase):
    def test_upload_download_and_list_use_configured_bucket(self) -> None:
        client = FakeS3Client()
        storage = S3DatasetStorage(client=client, bucket="production-bucket")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "movies.csv"
            source.write_text("movie_id,title\n1,Movie\n", encoding="utf-8")
            destination = Path(temporary) / "download" / "movies.csv"

            uri = storage.upload_file(
                local_path=source,
                prefix="data/raw/",
            )
            result = storage.download_file(
                prefix="data/raw/",
                object_name="movies.csv",
                destination=destination,
            )
            objects = list(storage.list_objects(prefix="data/raw/"))

        self.assertEqual(
            uri,
            "s3://production-bucket/data/raw/movies.csv",
        )
        self.assertEqual(result, destination)
        self.assertEqual(objects[0].size, 100)
        self.assertEqual(client.uploads[0][1:], ("production-bucket", "data/raw/movies.csv"))
        self.assertEqual(client.downloads[0][:2], ("production-bucket", "data/raw/movies.csv"))

    def test_rejects_parent_path_segments(self) -> None:
        storage = S3DatasetStorage(
            client=FakeS3Client(),
            bucket="production-bucket",
        )
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "movies.csv"
            source.write_text("data", encoding="utf-8")
            with self.assertRaises(ValueError):
                storage.upload_file(
                    local_path=source,
                    prefix="data/raw/",
                    object_name="../secret",
                )


if __name__ == "__main__":
    unittest.main()
