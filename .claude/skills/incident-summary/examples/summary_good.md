# Incident: payments-api latency, 2026-10-29

## Impact
- Charge requests timed out (504) for about 7 minutes, p99 above 31 seconds [L-1003]
- PaymentsLatencyHigh fired at 02:04 and resolved at 02:11 [L-1004] [L-1007]

## Timeline
- 02:01 payments-api v2.41.0 deployed, connection pool max reduced from 20 to 5 [L-1001]
- 02:03 requests waiting for a database connection began timing out [L-1002]
- 02:09 rollback to v2.40.3 started [L-1005]
- 02:11 alert resolved [L-1007]

## Suspected cause
- The pool size reduction in v2.41.0 starved requests of connections; the pool recovered after rollback [L-1001] [L-1006]
