"""Unit tests for dataset ingestion endpoints — Requirements 2.1–2.8."""
import io
import pytest
from unittest.mock import AsyncMock, patch

from app.core.security import create_access_token


def _auth(user):
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


# ── Upload ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_csv_returns_201(client, test_user):
    """Requirement 2.1: CSV upload succeeds and returns dataset record."""
    with patch("app.api.v1.datasets.upload_file", new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = "raw/user/id/file.csv"
        resp = await client.post(
            "/api/v1/datasets",
            headers=_auth(test_user),
            files={"file": ("data.csv", io.BytesIO(b"a,b\n1,2"), "text/csv")},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["format"] == "csv"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_json_returns_201(client, test_user):
    """Requirement 2.2: JSON upload succeeds."""
    with patch("app.api.v1.datasets.upload_file", new_callable=AsyncMock):
        resp = await client.post(
            "/api/v1/datasets",
            headers=_auth(test_user),
            files={"file": ("data.json", io.BytesIO(b'[{"a":1}]'), "application/json")},
        )
    assert resp.status_code == 201
    assert resp.json()["format"] == "json"


@pytest.mark.asyncio
async def test_upload_xlsx_returns_201(client, test_user):
    """Requirement 2.3: XLSX upload succeeds."""
    with patch("app.api.v1.datasets.upload_file", new_callable=AsyncMock):
        resp = await client.post(
            "/api/v1/datasets",
            headers=_auth(test_user),
            files={"file": ("data.xlsx", io.BytesIO(b"PK"), "application/octet-stream")},
        )
    assert resp.status_code == 201
    assert resp.json()["format"] == "xlsx"


@pytest.mark.asyncio
async def test_upload_unsupported_format_returns_422(client, test_user):
    """Requirement 2.5: unsupported format → 422 with supported formats listed."""
    resp = await client.post(
        "/api/v1/datasets",
        headers=_auth(test_user),
        files={"file": ("data.parquet", io.BytesIO(b"PAR1"), "application/octet-stream")},
    )
    assert resp.status_code == 422
    detail = str(resp.json())
    assert "csv" in detail


@pytest.mark.asyncio
async def test_upload_oversized_file_returns_413(client, test_user):
    """Requirement 2.4: file > 2 GB → 413."""
    big_data = b"x" * (2 * 1024 * 1024 * 1024 + 1)
    resp = await client.post(
        "/api/v1/datasets",
        headers=_auth(test_user),
        files={"file": ("big.csv", io.BytesIO(big_data), "text/csv")},
    )
    assert resp.status_code == 413


# ── List / Get ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_datasets_returns_own_only(client, test_user, admin_user, db_session):
    """Requirement 1.7: users only see their own datasets."""
    from app.db.models import Dataset
    # Create one dataset for test_user, one for admin_user
    ds1 = Dataset(user_id=test_user.id, name="mine.csv", format="csv", file_path="k1")
    ds2 = Dataset(user_id=admin_user.id, name="theirs.csv", format="csv", file_path="k2")
    db_session.add_all([ds1, ds2])
    await db_session.commit()

    resp = await client.get("/api/v1/datasets", headers=_auth(test_user))
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["items"]]
    assert ds1.id in ids
    assert ds2.id not in ids


@pytest.mark.asyncio
async def test_get_other_users_dataset_returns_403(client, test_user, admin_user, db_session):
    """Requirement 1.7: accessing another user's dataset → 403."""
    from app.db.models import Dataset
    ds = Dataset(user_id=admin_user.id, name="admin.csv", format="csv", file_path="k")
    db_session.add(ds)
    await db_session.commit()

    resp = await client.get(f"/api/v1/datasets/{ds.id}", headers=_auth(test_user))
    assert resp.status_code == 403


# ── Baseline ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_baseline_marks_dataset(client, test_user, db_session):
    """Requirement 8.3: setting baseline marks the dataset."""
    from app.db.models import Dataset
    ds = Dataset(user_id=test_user.id, name="base.csv", format="csv", file_path="k")
    db_session.add(ds)
    await db_session.commit()

    resp = await client.post(f"/api/v1/datasets/{ds.id}/baseline", headers=_auth(test_user))
    assert resp.status_code == 200
    assert resp.json()["is_baseline"] is True


# ── Jobs ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_job_returns_201(client, test_user, db_session):
    """Requirement 2.8: job submission returns job ID immediately."""
    from app.db.models import Dataset
    ds = Dataset(user_id=test_user.id, name="data.csv", format="csv", file_path="k")
    db_session.add(ds)
    await db_session.commit()

    with patch("app.api.v1.jobs.run_pipeline") as mock_task:
        mock_task.delay.return_value = None
        resp = await client.post(
            "/api/v1/jobs",
            headers=_auth(test_user),
            json={"dataset_id": ds.id, "pipeline_config": {}},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["status"] == "PENDING"
    mock_task.delay.assert_called_once()


@pytest.mark.asyncio
async def test_submit_job_for_other_users_dataset_returns_403(client, test_user, admin_user, db_session):
    """Requirement 1.7: cannot submit job for another user's dataset."""
    from app.db.models import Dataset
    ds = Dataset(user_id=admin_user.id, name="admin.csv", format="csv", file_path="k")
    db_session.add(ds)
    await db_session.commit()

    with patch("app.api.v1.jobs.run_pipeline"):
        resp = await client.post(
            "/api/v1/jobs",
            headers=_auth(test_user),
            json={"dataset_id": ds.id, "pipeline_config": {}},
        )
    assert resp.status_code == 403
