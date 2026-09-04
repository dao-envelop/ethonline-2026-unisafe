# Storage

The Substreams SQL sink writes into PostgreSQL. The schema lives **next to the manifest that references
it**, because `substreams.yaml` points at it by relative path and a second copy here would drift:

**[`schema.sql`](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/blob/master/schema.sql)**

Twelve tables — eleven event types plus `position_delta`, the one that actually models a position.

What is worth knowing without opening it:

- **Row identity is `(transaction_hash, log_index)`** — the log's position in the chain, not a synthetic
  id. That is what makes a replay idempotent: re-ingesting a block writes the same rows over the same
  keys instead of duplicating them.
- **Amounts are `numeric(78,0)`.** A `uint256` fits nothing narrower, and a float would round it
  silently — the one failure mode that never announces itself.
- **One schema per network** (`eth`, `arb`, `base`, `uni`) rather than a `chain_id` column: the sink runs
  one process per network with its own cursor, so "whose block 486482005 is this" is never a question.
- **`position_delta` is the position model**, and it has to be. The manager's own events cannot describe
  a position: `Allocated` carries a leg count, no manager event carries amounts, and for the volatile
  product nothing on chain links a position's salt to its pool. Uniswap's `ModifyLiquidity` log has all
  four facts together, and its `sender` is the manager.
- The sink's own `cursors` and `substreams_history` tables are **not** declared here: `substreams sink
  postgres setup` creates them, and they are how it resumes and unwinds reorgs.

The conventions are borrowed from the existing Envelop LP schema on purpose, so the two indexes can be
compared row by row.
