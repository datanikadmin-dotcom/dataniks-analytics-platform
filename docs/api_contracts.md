# API Contracts

## Webhook Server

Base URL: `http://localhost:8080` (dev) / `https://webhooks.client.example.com` (prod)

### POST /webhook

Accepts real-time events from source platforms.

**Headers:**
```
Content-Type: application/json
X-Webhook-Signature: <hmac-sha256-hex>
```

**Signature computation:**
```
HMAC-SHA256(WEBHOOK_SECRET, raw_request_body)
```

**Request body:**
```json
{
  "event_id": "evt_abc123",
  "event_type": "order.created",
  "timestamp": "2024-06-15T14:32:00Z",
  "data": { ... }
}
```

**Accepted event types:**
- `order.created`, `order.updated`, `order.cancelled`
- `payment.completed`, `payment.failed`, `payment.refunded`
- `inventory.updated`
- `shipment.created`, `shipment.updated`, `shipment.delivered`

**Responses:**

| Status | Meaning |
|---|---|
| 200 | Event accepted (or duplicate — idempotent) |
| 400 | Unknown event type or malformed body |
| 401 | Invalid HMAC signature |
| 422 | Missing required fields |
| 500 | Internal server error |

**Response body (200):**
```json
{
  "status": "accepted",
  "event_id": "evt_abc123"
}
```

### GET /health

```json
{ "status": "ok" }
```

---

## BaseConnector Interface

All source connectors implement this Python interface (`ingestion/base.py`).

```python
class BaseConnector(abc.ABC):

    def authenticate(self) -> None:
        """Authenticate with the source API. Called once on init."""

    def health_check(self) -> bool:
        """Return True if the source API is reachable."""

    def get_customers(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of customer records."""

    def get_products(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of product records."""

    def get_orders(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of order records."""

    def get_order_items(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of order-item records."""

    def get_payments(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of payment records."""

    def get_refunds(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of refund records."""

    def get_inventory(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of inventory snapshot records."""

    def get_shipments(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of shipment records."""

    def get_ad_spend(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of advertising spend records."""

    def get_payouts(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        """Yield DataFrames of payout records."""
```

**Ingestion metadata** (added automatically by `add_ingestion_metadata`):
- `_ingested_at: datetime` — UTC timestamp
- `_source: str` — connector identifier
- `_batch_id: str` — UUID per pipeline run
- `_record_hash: str` — MD5 of row payload

---

## BaseLLMProvider Interface

```python
class BaseLLMProvider(abc.ABC):

    @property
    def provider_name(self) -> str: ...

    def is_available(self) -> bool:
        """Return True if required API keys are present."""

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> LLMResponse: ...
```

**LLMResponse fields:**
```python
@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_in: int
    tokens_out: int
    raw: dict          # raw API response for debugging
```

---

## AnalystResponse

Returned by `DataNiksAnalyst.ask(question: str)`.

```python
@dataclass
class AnalystResponse:
    question: str
    answer: str
    sql: str           # empty string if no SQL was generated
    data: pd.DataFrame # empty DataFrame if no data returned
    row_count: int
    tokens_used: int
    safe: bool         # False if blocked by safety checks
    error: str         # empty string if no error
    metrics_detected: list[str]

    def to_dict(self) -> dict: ...
```
