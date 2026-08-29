"""
DataNiks Webhook Ingestion Server.

Accepts inbound events from source systems (order.created, payment.completed, …),
validates them, stores raw payloads in DuckDB, and queues them for processing.

Run locally:
    uvicorn ingestion.webhooks.server:app --host 0.0.0.0 --port 8080

In production:
    Deploy behind a reverse proxy; rotate WEBHOOK_SECRET regularly.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ingestion.loaders.duckdb_loader import DuckDBLoader

logger = logging.getLogger(__name__)

_WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-secret-not-for-prod")
_DB_PATH = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")

app = FastAPI(title="DataNiks Webhook Server", version="0.1.0")
_loader = DuckDBLoader(db_path=_DB_PATH)

ACCEPTED_EVENTS = {
    "order.created", "order.updated", "order.cancelled",
    "payment.completed", "payment.failed", "payment.refunded",
    "inventory.updated",
    "shipment.created", "shipment.updated", "shipment.delivered",
}


# ── Signature verification ─────────────────────────────────────────────────────

def _verify_signature(payload_bytes: bytes, signature: str | None, secret: str) -> bool:
    """
    HMAC-SHA256 verification.
    Expected header: X-DataNiks-Signature: sha256=<hex>
    """
    if not signature:
        return False
    if not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_dataniks_signature: str | None = Header(default=None),
    x_event_id: str | None = Header(default=None),
) -> JSONResponse:
    """
    Inbound webhook endpoint.

    Headers expected:
      X-DataNiks-Signature : sha256=<hmac> (required in production)
      X-Event-Id           : idempotency key (optional)
    """
    body = await request.body()

    # Signature check — skip in dev if secret is the placeholder value
    if _WEBHOOK_SECRET != "dev-secret-not-for-prod":
        if not _verify_signature(body, x_dataniks_signature, _WEBHOOK_SECRET):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    try:
        payload: dict[str, Any] = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload is not valid JSON",
        )

    event_type = payload.get("event_type") or payload.get("type")
    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing event_type field",
        )

    if event_type not in ACCEPTED_EVENTS:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": f"Unknown event_type: {event_type}",
                     "accepted": sorted(ACCEPTED_EVENTS)},
        )

    event_id = x_event_id or str(uuid.uuid4())
    received_at = datetime.now(timezone.utc).isoformat()

    # Idempotency check — if this event_id was already processed, skip
    existing = _loader.execute(
        f"SELECT COUNT(*) AS n FROM raw.webhook_events WHERE event_id = '{event_id}'"
        if _table_exists() else "SELECT 0 AS n"
    )
    if existing["n"].iloc[0] > 0:
        logger.info("[webhook] duplicate event_id=%s — skipping", event_id)
        return JSONResponse({"status": "duplicate", "event_id": event_id})

    # Store raw event
    row = pd.DataFrame([{
        "webhook_event_id":  str(uuid.uuid4()),
        "event_id":          event_id,
        "event_type":        event_type,
        "received_at":       received_at,
        "source":            payload.get("source", "unknown"),
        "payload":           json.dumps(payload),
        "processing_status": "pending",
        "processed_at":      None,
        "error_message":     None,
    }])

    _loader.load(row, table="webhook_events", schema="raw")
    logger.info("[webhook] stored event_id=%s type=%s", event_id, event_type)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "accepted", "event_id": event_id},
    )


def _table_exists() -> bool:
    try:
        result = _loader.execute(
            "SELECT COUNT(*) AS n FROM information_schema.tables "
            "WHERE table_schema='raw' AND table_name='webhook_events'"
        )
        return result["n"].iloc[0] > 0
    except Exception:
        return False
