# Security

## Secrets Management

- All credentials live in `.env` (never committed — in `.gitignore`)
- `.env.example` contains placeholder values with no real data
- In production, use a secrets manager (AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault) and inject at runtime
- Service-account JSON files must never be committed. Add `*.json` to `.gitignore` if adding credential files

## Webhook Security

The webhook server (`ingestion/webhooks/server.py`) validates every incoming request:

1. Reads the `X-Webhook-Signature` header
2. Computes `HMAC-SHA256(WEBHOOK_SECRET, raw_body)`
3. Compares using `hmac.compare_digest` (constant-time, prevents timing attacks)
4. Rejects with 401 if signature does not match
5. Checks idempotency: duplicate `event_id` returns 200 without reprocessing

Rotate `WEBHOOK_SECRET` quarterly and whenever team membership changes.

## AI Analyst SQL Safety

Two layers of protection:

### 1. Prompt injection block-list
`ai/assistant/core.py` checks `_is_blocked()` before any LLM call.
Blocked patterns include: `drop table`, `delete from`, `ignore previous instructions`,
`disregard your instructions`, `pretend you are`, `act as`.

Any match returns `AnalystResponse(safe=False)` immediately — no LLM call, no SQL.

### 2. SQL validator
`ai/queries/validator.py` runs after LLM generates SQL.
Rules:
- Query must start with `SELECT` or `WITH`
- Any occurrence of: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE,
  REPLACE, MERGE, CALL, EXEC, EXECUTE, GRANT, REVOKE, ATTACH, DETACH, COPY,
  EXPORT, IMPORT → rejected with reason
- Rejected SQL is never executed

## API Credentials

Source connectors receive credentials via config, not environment interpolation at connector level.
The `config/sources.yaml` file itself uses `${ENV_VAR}` references; actual values come from `.env`.

Connectors must:
- Use read-only API scopes/keys
- Never log credential values
- Use HTTPS for all API calls

## Data Privacy

- Customer PII (email, name, address) exists in `dim_customer` and `stg_customers`
- In production, apply column-level masking or row-level security in BigQuery if required by GDPR/CCPA
- The AI Analyst query results may include PII if the LLM generates a query over customer data — consider a PII-scrubbing post-processor in regulated environments
- Synthetic demo data uses Faker — no real PII

## Access Control

| Layer | Mechanism |
|---|---|
| DuckDB (dev) | File system permissions |
| BigQuery (prod) | IAM roles: dataViewer for BI, dataEditor for pipeline |
| Power BI | Workspace roles (Admin / Member / Contributor / Viewer) |
| Airflow | RBAC — restrict DAG trigger to pipeline operators |
| Webhook endpoint | HMAC-SHA256 + firewall allowlist (source IP) |

## Dependency Security

Run dependency audit before each client deployment:
```bash
python3 -m pip audit
```

Pin all dependencies in `requirements.txt` to specific versions for reproducibility.
