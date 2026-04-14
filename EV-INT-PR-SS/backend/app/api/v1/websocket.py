"""WebSocket endpoint for real-time job progress — Requirement 11.5."""
import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from app.core.security import decode_token
from app.db.redis import get_redis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(websocket: WebSocket, job_id: str):
    token = websocket.query_params.get("token", "")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    redis = get_redis()

    try:
        last_progress = -1
        last_status = ""

        # Try pubsub first; fall back to polling if not supported
        has_pubsub = hasattr(redis, "pubsub")
        pubsub = None

        if has_pubsub:
            try:
                pubsub = redis.pubsub()
                await pubsub.subscribe(f"job:{job_id}")
            except Exception:
                pubsub = None
                has_pubsub = False

        while True:
            try:
                # Always poll Redis key for current progress
                current = await redis.get(f"job_status:{job_id}")
                if current is not None:
                    progress = int(current)
                    if progress != last_progress:
                        last_progress = progress
                        await websocket.send_text(json.dumps({
                            "job_id": job_id,
                            "progress": progress,
                            "status": "RUNNING" if progress < 100 else "COMPLETED",
                        }))
                        if progress >= 100:
                            break

                # Also check pubsub if available
                if pubsub:
                    try:
                        msg = await asyncio.wait_for(
                            pubsub.get_message(ignore_subscribe_messages=True),
                            timeout=0.1
                        )
                        if msg and msg.get("data"):
                            data = msg["data"]
                            if isinstance(data, bytes):
                                data = data.decode()
                            parsed = json.loads(data)
                            if not parsed.get("ping"):
                                await websocket.send_text(data)
                                if parsed.get("status") in ("COMPLETED", "FAILED"):
                                    break
                    except (asyncio.TimeoutError, Exception):
                        pass

                await asyncio.sleep(1.0)

            except asyncio.TimeoutError:
                try:
                    await websocket.send_text(json.dumps({"ping": True}))
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info("WS client disconnected from job %s", job_id)
    except Exception as exc:
        logger.error("WS error on job %s: %s", job_id, exc)
    finally:
        if pubsub:
            try:
                await pubsub.unsubscribe(f"job:{job_id}")
                await pubsub.aclose()
            except Exception:
                pass
