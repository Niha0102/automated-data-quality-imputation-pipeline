"""
Property tests for dataset ingestion.

Feature: ai-data-quality-platform
Validates: Requirements 2.5
"""
import io
import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from unittest.mock import patch, AsyncMock

from app.core.security import create_access_token

h_settings.register_profile("ci", max_examples=50)
h_settings.load_profile("ci")

# Extensions that are NOT in the supported set
_UNSUPPORTED_EXT = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
    min_size=1,
    max_size=6,
).filter(lambda ext: ext.lower() not in {"csv", "json", "xlsx"})


@pytest.mark.asyncio
async def test_unsupported_format_returns_422_property(client, test_user):
    """For a sample of unsupported extensions, upload returns HTTP 422.
    Validates: Requirements 2.5"""
    unsupported_exts = ["parquet", "xml", "txt", "pdf", "zip", "tar", "py", "sql", "tsv", "avro"]
    token = create_access_token(test_user.id, test_user.role)

    for ext in unsupported_exts:
        filename = f"data.{ext}"
        resp = await client.post(
            "/api/v1/datasets",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (filename, io.BytesIO(b"col1,col2\n1,2"), "application/octet-stream")},
        )
        assert resp.status_code == 422, (
            f"Expected 422 for extension '.{ext}', got {resp.status_code}"
        )
        detail = str(resp.json())
        assert any(fmt in detail for fmt in ["csv", "json", "xlsx"])
