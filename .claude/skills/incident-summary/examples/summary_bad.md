# Incident: payments-api latency, 2026-10-29

## Impact
- Charge requests timed out (504) for about 7 minutes [L-1003]
- Roughly 4,000 customers saw failed payments

## Timeline
- 02:01 payments-api v2.41.0 deployed [L-1001]
- 02:06 database failed over to the replica [L-9999]
