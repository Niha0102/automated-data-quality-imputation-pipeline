"""Local disk storage — replaces S3/MinIO for local dev."""
import pathlib

_BASE = pathlib.Path(__file__).parent.parent.parent / "local_uploads"


def _path(bucket: str, key: str) -> pathlib.Path:
    p = _BASE / bucket / key
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


async def upload_file(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    _path(bucket, key).write_bytes(data)
    return key


async def delete_file(bucket: str, key: str) -> None:
    try:
        _path(bucket, key).unlink(missing_ok=True)
    except Exception:
        pass


def generate_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    return f"http://localhost:8000/local-files/{bucket}/{key}"


def read_file(bucket: str, key: str) -> bytes:
    p = _path(bucket, key)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {bucket}/{key}")
    return p.read_bytes()


def file_exists(bucket: str, key: str) -> bool:
    return _path(bucket, key).exists()
