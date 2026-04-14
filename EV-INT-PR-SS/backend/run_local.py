"""
Local dev runner — SQLite + in-memory stubs + inline pipeline (no Docker needed).
Usage: python run_local.py
"""
import os, sys, threading

# ── Env overrides (must be before any app imports) ────────────────────────────
os.environ["DATABASE_URL"]   = "sqlite+aiosqlite:///./local_dev.db"
os.environ["JWT_SECRET_KEY"] = "local_dev_secret_key_not_for_production"
os.environ["ENVIRONMENT"]    = "development"
os.environ["CORS_ORIGINS"]   = '["http://localhost:3000"]'
os.environ["LOCAL_STORAGE"]  = "1"

# ── Redis stub ────────────────────────────────────────────────────────────────
import app.db.redis as _redis_mod
from app.db.redis_stub import get_stub_redis

_stub_redis = get_stub_redis()
_redis_mod._redis = _stub_redis
_redis_mod.get_redis = lambda: _stub_redis

async def _noop_close(): pass
_redis_mod.close_redis = _noop_close

async def _cache_set(k, v, ttl):  await _stub_redis.setex(k, ttl, v)
async def _cache_get(k):          return await _stub_redis.get(k)
async def _cache_del(k):          await _stub_redis.delete(k)
async def _rate_incr(uid):
    k = f"rate_limit:{uid}"
    return await _stub_redis.incr(k)

_redis_mod.cache_set            = _cache_set
_redis_mod.cache_get            = _cache_get
_redis_mod.cache_delete         = _cache_del
_redis_mod.increment_rate_limit = _rate_incr

# ── Local disk storage (replaces S3/MinIO) ────────────────────────────────────
import app.services.storage as _storage_mod
from app.services.local_storage import (
    upload_file as _local_upload,
    delete_file as _local_delete,
    generate_presigned_url as _local_presigned,
    read_file as _local_read,
)
_storage_mod.upload_file           = _local_upload
_storage_mod.delete_file           = _local_delete
_storage_mod.generate_presigned_url = _local_presigned

# ── In-memory MongoDB (stores reports in a dict) ──────────────────────────────
import app.db.mongo as _mongo_mod

_reports_store: dict = {}

class _MemCol:
    def __init__(self, store: dict):
        self._s = store

    async def insert_one(self, doc):
        key = str(doc.get("_id", id(doc)))
        self._s[key] = dict(doc)
        return type("R", (), {"inserted_id": key})()

    async def find_one(self, q=None, *a, **kw):
        if q and "_id" in q:
            return self._s.get(str(q["_id"]))
        return None

    def find(self, *a, **kw): return self
    async def to_list(self, *a, **kw): return list(self._s.values())
    async def update_one(self, q, upd, *a, **kw):
        if "_id" in q and str(q["_id"]) in self._s and "$set" in upd:
            self._s[str(q["_id"])].update(upd["$set"])
    async def delete_one(self, q=None, *a, **kw):
        if q and "_id" in q:
            self._s.pop(str(q["_id"]), None)

_reports_col = _MemCol(_reports_store)

class _StubDB:
    def __getitem__(self, n): return _reports_col if n == "reports" else _MemCol({})
    def get_collection(self, n): return self[n]

class _StubMongo:
    def get_default_database(self): return _StubDB()
    def close(self): pass

_stub_mongo = _StubMongo()
_mongo_mod._client              = _stub_mongo
_mongo_mod.get_mongo_client     = lambda: _stub_mongo
_mongo_mod.get_mongo_db         = lambda: _stub_mongo.get_default_database()
_mongo_mod.reports_collection   = lambda: _reports_col
_mongo_mod.logs_collection      = lambda: _MemCol({})
async def _noop_mongo(): pass
_mongo_mod.close_mongo_client   = _noop_mongo

# ── Inline pipeline (replaces Celery worker) ──────────────────────────────────
import app.tasks.pipeline_task as _task_mod

# Add ml_pipeline to sys.path
_ml_path = os.path.join(os.path.dirname(__file__), "..", "ml_pipeline")
if _ml_path not in sys.path:
    sys.path.insert(0, _ml_path)


def _run_pipeline_thread(job_id: str, dataset_id: str, user_id: str, config: dict):
    import asyncio, io, json, uuid
    from datetime import datetime, timezone

    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from sqlalchemy import text

        engine  = create_async_engine("sqlite+aiosqlite:///./local_dev.db", echo=False)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async def upd(session, **kw):
            sets   = ", ".join(f"{k} = :{k}" for k in kw)
            params = {"job_id": job_id, **kw}
            await session.execute(text(f"UPDATE jobs SET {sets} WHERE id = :job_id"), params)
            await session.commit()
            if "progress" in kw:
                await _stub_redis.setex(f"job_status:{job_id}", 86400, str(kw["progress"]))

        async with factory() as session:
            try:
                await upd(session, status="RUNNING", progress=0)

                # Load file
                row = (await session.execute(
                    text("SELECT file_path, format FROM datasets WHERE id = :id"), {"id": dataset_id}
                )).fetchone()
                if not row:
                    raise ValueError(f"Dataset {dataset_id} not found")

                raw = _local_read("adqip-datasets", row.file_path)
                import pandas as pd
                if row.format == "csv":
                    df = pd.read_csv(io.BytesIO(raw))
                elif row.format == "json":
                    df = pd.read_json(io.BytesIO(raw))
                elif row.format == "xlsx":
                    df = pd.read_excel(io.BytesIO(raw))
                else:
                    raise ValueError(f"Unsupported format: {row.format}")

                await upd(session, progress=5)

                from pipeline.profiler import profile_dataframe
                profile = profile_dataframe(df)
                await upd(session, progress=15)

                from pipeline.scorer import compute_quality_score
                await upd(session, progress=20)

                from pipeline.imputer import impute
                imp = impute(df, strategy=config.get("impute_strategy", "auto"))
                df  = imp.df
                issues, fixes = [], []
                if imp.flagged_columns:
                    issues.append(f"Columns with >80% missing: {imp.flagged_columns}")
                if imp.strategy_used:
                    fixes.append(f"Imputed missing values in: {list(imp.strategy_used.keys())}")
                await upd(session, progress=30)

                from pipeline.outlier_detector import detect_and_handle
                out = detect_and_handle(df, handling=config.get("outlier_handling", "cap"))
                df  = out.df_cleaned
                n_out = sum(r.outlier_count for r in out.reports)
                if n_out:
                    issues.append(f"Detected {n_out} outlier(s)")
                    fixes.append("Applied cap strategy to outliers")
                await upd(session, progress=40)

                from pipeline.transformer import fit_transform
                df_transformed = df
                try:
                    tr, _ = fit_transform(df, scaler="standard", encode="onehot")
                    df_transformed = tr.df
                    fixes.append("Applied standard scaling and one-hot encoding")
                except Exception as e:
                    print(f"[LOCAL] Transform skipped: {e}")
                await upd(session, progress=55)

                anomaly_dict = {}
                if len(df_transformed) >= 20:
                    try:
                        from pipeline.anomaly_detector import AutoencoderDetector
                        det = AutoencoderDetector(epochs=10)
                        det.fit(df_transformed)
                        ar  = det.predict(df_transformed)
                        anomaly_dict = {"anomaly_count": ar.anomaly_count, "anomaly_pct": ar.anomaly_pct}
                        if ar.anomaly_count:
                            issues.append(f"Detected {ar.anomaly_count} anomalous records ({ar.anomaly_pct:.1f}%)")
                    except Exception as e:
                        print(f"[LOCAL] Anomaly detection skipped: {e}")
                await upd(session, progress=65)
                await upd(session, progress=75)  # drift skipped (no baseline)

                final = compute_quality_score(df)
                await upd(session, progress=80)

                from ai.advisor import AIAdvisor
                adv = AIAdvisor()
                profile_dict = {
                    "columns": [
                        {"name": c.name, "dtype": c.dtype, "missing_pct": c.missing_pct,
                         "cardinality": c.cardinality, "mean": c.mean, "std": c.std,
                         "top_values": c.top_values}
                        for c in profile.columns
                    ],
                    "row_count": profile.row_count,
                    "column_count": profile.column_count,
                }
                semantic_types   = adv.infer_column_semantics(profile_dict)
                narrative        = adv.generate_narrative(issues, fixes)
                recommendations  = adv.suggest_transformations(profile_dict)
                await upd(session, progress=88)

                # Save report to in-memory MongoDB
                await _reports_col.insert_one({
                    "_id": job_id,
                    "job_id": job_id,
                    "dataset_id": dataset_id,
                    "quality_score": final.overall,
                    "completeness": final.completeness,
                    "consistency": final.consistency,
                    "accuracy": final.accuracy,
                    "profile": profile_dict,
                    "issues": issues,
                    "fixes": fixes,
                    "recommendations": recommendations,
                    "semantic_types": semantic_types,
                    "narrative": narrative,
                    "anomaly_summary": anomaly_dict,
                    "drift_summary": {},
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                await upd(session, progress=95)

                # Save dataset version
                vnum = (await session.execute(
                    text("SELECT COALESCE(MAX(version_number),0)+1 FROM dataset_versions WHERE dataset_id=:d"),
                    {"d": dataset_id}
                )).scalar_one()
                buf = io.BytesIO()
                df.to_csv(buf, index=False)
                ckey = f"cleaned/{dataset_id}/v{vnum}/{job_id}.csv"
                await _local_upload("adqip-datasets", ckey, buf.getvalue(), "text/csv")

                now_str = datetime.now(timezone.utc).isoformat()
                await session.execute(text(
                    "INSERT INTO dataset_versions (id,dataset_id,version_number,job_id,file_path,transform_params,quality_score,created_at) "
                    "VALUES (:id,:did,:vnum,:jid,:fp,:tp,:qs,:ca)"
                ), {"id": str(uuid.uuid4()), "did": dataset_id, "vnum": vnum, "jid": job_id,
                    "fp": ckey, "tp": json.dumps({}), "qs": final.overall, "ca": now_str})
                await session.execute(text(
                    "UPDATE datasets SET row_count=:rc, column_count=:cc WHERE id=:did"
                ), {"rc": len(df), "cc": len(df.columns), "did": dataset_id})
                await session.commit()

                # Alert if quality low
                if final.overall < 70.0:
                    await session.execute(text(
                        "INSERT INTO alerts (id,user_id,job_id,type,message,is_resolved,created_at) "
                        "VALUES (:id,:uid,:jid,:t,:m,:r,:ca)"
                    ), {"id": str(uuid.uuid4()), "uid": user_id, "jid": job_id,
                        "t": "quality_drop",
                        "m": f"Quality score {final.overall:.1f}% is below threshold 70%",
                        "r": False, "ca": now_str})
                    await session.commit()

                await upd(session, status="COMPLETED", progress=100)
                print(f"[LOCAL] ✓ Pipeline done — job {job_id[:8]} score={final.overall:.1f}%")

            except Exception as exc:
                import traceback; traceback.print_exc()
                try:
                    await upd(session, status="FAILED", error_message=str(exc)[:500])
                except Exception:
                    pass

        await engine.dispose()

    asyncio.run(_run())


class _InlineTask:
    def delay(self, job_id, dataset_id, user_id, config):
        print(f"[LOCAL] → Queuing pipeline for job {job_id[:8]}…")
        threading.Thread(
            target=_run_pipeline_thread,
            args=(job_id, dataset_id, user_id, config),
            daemon=True,
        ).start()
        return type("R", (), {"id": job_id})()

_task_mod.run_pipeline = _InlineTask()

# ── Create SQLite tables + seed users ─────────────────────────────────────────
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.db.models import Base, User
from app.core.security import hash_password


async def _setup_db():
    engine = create_async_engine("sqlite+aiosqlite:///./local_dev.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        if not (await s.execute(select(User).where(User.email == "admin@demo.com"))).scalar_one_or_none():
            s.add(User(email="admin@demo.com", password_hash=hash_password("admin123"), role="admin", is_active=True))
        if not (await s.execute(select(User).where(User.email == "user@demo.com"))).scalar_one_or_none():
            s.add(User(email="user@demo.com",  password_hash=hash_password("user123"),  role="user",  is_active=True))
        await s.commit()
    await engine.dispose()
    print("[LOCAL] DB ready  →  local_dev.db")
    print("[LOCAL] admin@demo.com / admin123")
    print("[LOCAL] user@demo.com  / user123")

asyncio.run(_setup_db())

# ── Start uvicorn ─────────────────────────────────────────────────────────────
import uvicorn
from app.main import app

print("\n[LOCAL] Backend  → http://localhost:8000")
print("[LOCAL] API docs → http://localhost:8000/docs")
print("[LOCAL] Frontend → http://localhost:3000\n")

uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
