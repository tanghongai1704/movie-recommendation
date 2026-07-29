from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


class S3StorageError(RuntimeError):
    """Raised when a configured S3 transfer fails."""


@dataclass(frozen=True)
class S3Object:
    key: str
    size: int
    etag: str | None


class S3DatasetStorage:
    """Real S3 upload/download boundary for datasets and model artifacts."""

    def __init__(self, *, client: Any, bucket: str) -> None:
        if not bucket.strip():
            raise ValueError("S3 bucket must not be empty")
        self._client = client
        self._bucket = bucket

    def upload_file(
        self,
        *,
        local_path: Path,
        prefix: str,
        object_name: str | None = None,
    ) -> str:
        source = Path(local_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        key = self._key(prefix, object_name or source.name)
        try:
            self._client.upload_file(str(source), self._bucket, key)
        except Exception as exc:
            raise S3StorageError("Unable to upload file to Amazon S3") from exc
        return f"s3://{self._bucket}/{key}"

    def download_file(
        self,
        *,
        prefix: str,
        object_name: str,
        destination: Path,
    ) -> Path:
        target = Path(destination)
        key = self._key(prefix, object_name)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            self._client.download_file(self._bucket, key, str(target))
        except Exception as exc:
            raise S3StorageError(
                "Unable to download file from Amazon S3"
            ) from exc
        return target

    def list_objects(self, *, prefix: str) -> Iterator[S3Object]:
        token: str | None = None
        try:
            while True:
                options: dict[str, Any] = {
                    "Bucket": self._bucket,
                    "Prefix": prefix,
                }
                if token:
                    options["ContinuationToken"] = token
                response = self._client.list_objects_v2(**options)
                for item in response.get("Contents", []):
                    yield S3Object(
                        key=item["Key"],
                        size=int(item.get("Size", 0)),
                        etag=item.get("ETag"),
                    )
                if not response.get("IsTruncated"):
                    return
                token = response["NextContinuationToken"]
        except Exception as exc:
            raise S3StorageError("Unable to list Amazon S3 objects") from exc

    @staticmethod
    def _key(prefix: str, object_name: str) -> str:
        relative = PurePosixPath(object_name.replace("\\", "/"))
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
        ):
            raise ValueError("S3 object name must be a safe relative path")
        return (
            f"{prefix.rstrip('/')}/{relative.as_posix()}"
            if prefix
            else relative.as_posix()
        )
