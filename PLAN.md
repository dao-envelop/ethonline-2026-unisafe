# Plan and progress log

The working plan for our ETHOnline 2026 entry, kept public on purpose: judges asked for a transparent
process, so this file states what we intend to build **before** we build it, and records what actually
landed underneath. Where reality disagrees with the plan, the plan gets corrected rather than quietly
rewritten.

Event: 4–13 September 2026, submission deadline **13 September, 12:00 EDT**.
Track: **Continuity — Extend Open Source**. See [What existed before](README.md#what-existed-before-the-hackathon).

---

## The thing we are building

An operator of a unisafe manager can rebalance a position but can never withdraw — the contract, not
trust, enforces that, and operator swaps are additionally checked against a Chainlink feed. What an
operator cannot do today is move capital to a *different pool* atomically. That takes two transactions,
`withdrawTo` then `allocate`, and between them the capital sits idle.

`moveLiquidity` collapses that into one call: free a position in one pool and re-deploy it in another,
inside a single Uniswap v4 `unlock`, with one settlement pass.

Around it, four supporting pieces that together make the operation usable by an agent rather than only
by a human reading a block explorer:

```
 indexed events ──▶ hosted read/strategy service ──▶ ranks pools, suggests a move
   (Substreams)              (HTTP MCP)                          │
                                                                 ▼
                                             local MCP: re-derives, checks policy,
                                             simulates, signs  ──▶  moveLiquidity
                                                                        │
                                                          Chainlink-guarded swaps
```

## Design decisions, and why

**The local agent server holds the key and nothing else.** Our MCP server had grown to carry position
history, yield maths and data fetching alongside the keystore. That is the wrong shape for something
running on a user's machine: its job is to build calldata, check it against policy, simulate it and sign.
Everything that is knowledge about the market moves to a hosted service. The consequence worth stating:
after the split the key-holding process makes **no outbound HTTP call except RPC**, so "the service cannot
hand you calldata to sign" stops being a promise in the documentation and becomes a property of the
architecture. A compromised or simply wrong service can suggest a bad move; it cannot sign one, and the
local side re-derives every parameter and re-checks it against chain state before anything is broadcast.

**The index is the primary read path, with fallbacks under it.** Reads go Substreams/The Graph → our
existing event oracle → direct log scan. The oracle is proven in production and stays as automatic
degradation, but the normal path is the index — otherwise "we use The Graph" would be decoration. Four
conditions come with making a fresh index primary, and none of them are optional: degradation must be
automatic rather than a manual switch; every indexed answer must carry the block it is current as of, so
"nothing happened" is distinguishable from "not caught up"; a config flag must be able to demote the index
in one field; and the two paths must be reconciled against a real manager before release.

**Everything new is guarded the same way as everything old.** `moveLiquidity` reuses the existing swap
guard, the existing range and liquidity floors, and the existing settlement. It deliberately has **no
recipient parameter** — there is no path out of the contract, which is a structural guarantee rather than
a check that could be forgotten. It widens the operator's *radius* (recenter moves within one pool, move
crosses pools of the owner-fixed set) without widening the *class* of things an operator may do.

---

## Workstreams

### A — `moveLiquidity`

**Repo:** [uni-smart-wallet](https://github.com/dao-envelop/uni-smart-wallet) · branch `task/051-cross-pool-move`

One new operator entry point on `VolatileLPManager` (and its `OpenVolatileLPManager` subclass; the
stablecoin manager is deliberately untouched — its range is fixed at init and the operation does not fit
its model). Handler shape: free the source position, re-deploy through the existing allocate path — which
already carries the pre-swap, the full-fill guard, the minimum-out floor and the oracle check — then
settle once.

Why it is legal in v4, and why we checked before writing it: deltas are keyed by `(address, currency)`
rather than by pool, and `unlock` verifies exactly one thing on exit — that no non-zero delta remains.
Nothing restricts a callback to one pool. We proved it with a standalone test that moves liquidity across
two pools, and across three with an intermediate swap, in one `unlock`, plus a negative test that leaving
a currency unsettled reverts the whole thing.

Two things this must get right that the existing code got wrong:

- **Report realised fees.** Removing liquidity in v4 realises accrued fees. Our recenter path does that
  and reports nothing, which makes lifetime fee counters silently reset. The new operation emits the
  amounts from its first commit, reusing the existing fee event so consumers need no changes.
- **Make the spend cap apply.** The agent-side policy computes a per-token spend only for allocate, so
  its per-transaction cap does not currently bite on any other operation. Moving across two pools makes
  that gap obvious; the fix is to make each operation report its own spend.

**Hard constraint:** EIP-170. The volatile manager had 858 bytes of headroom and its subclass 918, and
because the subclass inherits everything, every byte is spent twice.

**What that constraint decided (4 Sep).** The intended shape — arrays of pulls and arrays of adds — cost
947 bytes against 858, because arrays of structs need their own calldata-to-memory encoder and memory
decoder. The operation therefore takes **one source and one destination**; an operator repeats the call to
move several positions. Deduplicating the swap path returned 233 bytes and paid for the rest. Final:
Volatile 24,432 (144 free), OpenVolatile 24,372 (204), Stable 24,178 (398).

### B — Substreams package

**Repo:** [substreams-uniswap-v4-lp](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp)

A reusable package that decodes the event surface of the *class* "LP manager on top of Uniswap v4" into
typed protobuf — one message type per event, never raw bytes or JSON — with a store keyed off manager
creation so it works for any manager the factory produced rather than a hardcoded address list.

The non-obvious part, which is why this is a package and not a script: positions cannot be reconstructed
from manager events alone. The allocate event carries only a leg count, no manager event carries amounts,
and for the volatile product there is no on-chain link from a position's salt to its pool. The model has
to be built on Uniswap's own `ModifyLiquidity` logs, where pool, range, exact liquidity delta and salt all
appear together — which also makes a recenter decompose for free into a removal row and an addition row.

It emits both a SQL sink output and a subgraph output, so the same package feeds a database and a
Subgraph Studio deployment.

### C — Local MCP server, slimmed

**Repo:** [unisafe](https://github.com/dao-envelop/unisafe) · package `@envelop/mcp-lp`

Keeps: keystore and signing, the policy guard, the propose → simulate → execute loop, calldata building,
and the handful of on-chain reads needed to build and verify a transaction. Gains `propose_move` /
`execute_move`. Loses history, operator enumeration and portfolio valuation to D.

This is a breaking release of a published package, so it comes with the chores: the documentation gate
that cross-checks the tool list, the aligned versions across package, plugin and marketplace entry, and a
changelog entry saying where the moved tools went.

### D — Hosted read/strategy service

**Repo:** [unisafe](https://github.com/dao-envelop/unisafe)

One process, two surfaces: MCP over streamable HTTP, and plain REST for the frontend. No keys, read-only,
cacheable, shared. Serves position history, realised yield, impermanent loss, fee series, operator lists,
pool ranking by yield, and `suggest_move` — which returns plain numbers, never calldata.

Runs on our own server behind Cloudflare, alongside the database the Substreams sink writes to.

### E — Arc deployment

**Repo:** [uni-smart-wallet](https://github.com/dao-envelop/uni-smart-wallet)

Deploy the factory, both volatile implementations, the lens, the descriptor and the Chainlink oracle to
Arc (chain 5042), wire the feeds, seed a USDC/EURC pool, and add the network to the frontend.

Three properties of Arc that the code has to be checked against, because our currency handling was written
with ETH in mind: USDC is the native gas token and exists simultaneously as an 18-decimal native balance
and a 6-decimal ERC-20 predeploy over the *same* balance; there is no WETH9; and blocks are roughly half a
second, which matters for how long a proposed transaction stays valid.

---

## Schedule

| Date | Work |
|---|---|
| 4–5 Sep | A: contract, tests, size measurement |
| 5–7 Sep | B: protobuf, modules, package, sink. D: service skeleton and infrastructure |
| 8 Sep | D: service deployed. B: subgraph output if time allows |
| 9 Sep | D: index as primary read path with fallbacks, pool ranking, `suggest_move` |
| 10 Sep | C: local server slimmed, `move` tools, release chores |
| 11 Sep | E: Arc |
| 12 Sep | `FEEDBACK.md`, architecture diagrams, demo video |
| 13 Sep | Submission |

If time runs short we cut in this order: the subgraph output, then the optional third-pool swap array,
then the Arc frontend. The one thing we do not cut is Substreams indexing Arc — no other index covers that
chain, and it is where the data genuinely comes from nowhere else.

## Things that could stop us

- **Contract size.** The only real technical risk in A. Mitigated by calling existing internals instead of
  copying them, and by an external library we can push helpers into.
- **Arc's dual-representation native USDC.** Could surface late, which is why Arc is scheduled last.
- **A fresh index in front of a proven one**, on a tool that signs real transactions. Mitigated by the four
  conditions listed above; without all four we do not promote it.
- **Free-tier block quota.** Sub-second-block chains consume block quota fast, so the index covers the
  chains it can afford and the oracle remains primary on the rest. Stated in the README rather than left
  as an accident of configuration.
- **Existing managers do not get the new operation.** Deployed managers are non-upgradeable clones; the
  operation only exists on managers created after the new implementation ships. We say so out loud rather
  than letting a demo imply otherwise.

---

## Progress log

Updated as work lands. Each entry links the commits that produced it.

| Workstream | Status | Landed |
|---|---|---|
| A — `moveLiquidity` | ✅ implemented and deployed | `5a77c41` → `cc7d732`, in `master`; deploy `520f542` (8 Sep) |
| B — Substreams package | ✅ sink live; `graph_out` landed | `1803105` → `7bac861`, release `v0.2.0` |
| C — local MCP slimmed | 🟡 written, awaiting merge + release | `84bc0bb` on `task/088-mcp-slim-move` |
| D — hosted service | ✅ live in production | `task/087` + `task/089`, deployed from CI |
| E — Arc deployment | ⬜ not started | — |
| Demo video | ⬜ not started | — |

**8 Sep — the contracts are on chain, and `graph_out` makes the composition real.**

New `StableLPManager`, `VolatileLPManager`, `UniLens` and `ChainlinkPriceOracle` implementations are
deployed on all five chains (release 2.1.0). `moveLiquidity` therefore exists on chain — for managers
created from this release onward, which is what non-upgradeable clones mean and what the demo has to say
out loud. The frontend and the local MCP server follow the new addresses, and the sync that does it now
*accumulates* implementations instead of replacing them: two places recognise a manager by the
implementation it was cloned from, and filtering by the newly deployed pair alone would have emptied the
manager list for every existing owner the moment the oracle API was unavailable.

`graph_out` emits `EntityChanges` from the same modules that feed the SQL sink — which is what makes the
composition claim structural rather than a sentence in a README: two Graph products, one decoder. The
subgraph model is not the SQL shape. Postgres keeps eleven event tables plus `position_delta` because
that schema exists in production and its rows are compared against it; the subgraph gets `Manager`,
`Operator` already folded into "who may act now", `Position` with running liquidity and lifetime fees,
an immutable `PositionDelta`, and one `ManagerEvent` timeline over all eleven event types.

Verified live on **Unichain** — one of the two chains this package follows, alongside mainnet, while
Arbitrum stays on the Envelop oracle because a per-block quota and 0.25-second blocks are bad
arithmetic. Manager `0x9f7e19b7…` at block 54,551,071 comes out as a single entity with its
`Initialized` fields merged in rather than a create and an update racing inside one block; the first
allocate at 54,572,737 produces the `Position`, its `PositionDelta` and an `allocated` event. Both runs
started at the package's own `initialBlock` for that chain, so nothing was spent backfilling stores
through the hosted endpoint.

One dependency did not survive contact: `substreams-entity-change`, the helper crate for exactly this
job, pins `substreams` 0.6 while this package is on 0.7 — both versions end up linked, and with
`lto = true` the build fails outright. The entity types are generated from a local copy of the upstream
proto instead, while the manifest still imports the official `.spkg` so the descriptor a consumer reads
stays canonical.

**5 Sep — D is in production.** The hosted service answers on `unisafe.envelop.is` (`/mcp` for agents,
`/v2` for the app, `/healthz`), deployed by the CI job rather than by hand, reading the index over TLS.
It is mounted on the existing host under its own paths rather than a subdomain of its own: Cloudflare's
Universal SSL covers one level of subdomain, so `mcp.unisafe.envelop.is` would have failed the handshake
at the edge.

**6 Sep — the index was primary for a chain it had no business answering for.** `INSIGHT_SCHEMAS` merged
over a hardcoded default map, so it could add a network but never remove one: setting it to
`1:eth,130:uni` left `42161 → arb` in place, and production served Arbitrum history from a one-off
historical window as `source: "graph"` with an empty degradation trail. It now replaces the map rather
than merging into it, and the startup line prints the active pairs so acceptance is checked from the log
instead of by probing a reference manager.

**4 Sep — C written, deliberately not published.** The local server is now the half that holds the key
and nothing else: `get_position_history`, `list_operators` and `get_portfolio` left for the hosted
service, and `propose_move` / `execute_move` arrived. After the split it makes **no outbound HTTP call
except RPC** — which is the whole point, because "a remote service cannot hand you calldata to sign"
stops being a promise in the documentation and becomes a property of the architecture.

`propose_move` refuses a destination outside the manager's configured pools rather than building a
proposal that cannot execute: the set is fixed when the manager is created and the contract reverts
`UnknownPool` for anything else. The planner needed its own file, because a move gets its numbers from a
different place than a recenter — the contract sizes a recenter from the freed deltas it measures itself,
while a move goes through the allocate path and sizes from `amount*Desired` supplied by the caller. So
the caller has to predict what the position frees, declare what it holds *after* any pre-swap rather than
before, and shade the result down: declaring more than the manager ends up holding reverts the whole
unlock, declaring less leaves a few basis points idle for the next allocate.

A real defect fixed on the way: `policy.maxAmountPerTx` only ever populated for `allocate`, so the one
quantitative limit in a default-deny policy did nothing on recenter — which moves an entire principal —
nor on claim or reinvest. It now applies everywhere, and what it measures is stated: **how much moves in
one transaction**, not how much leaves, since an operator has no path outward at all and a cap on outflow
would bound a number that is always zero.

**Not published, on purpose.** Versions are aligned at 1.0.0 and the plugin declares both servers, but
the registry release waits until the hosted service is actually answering — publish first and users lose
their history between two releases.

**4 Sep — D packaged and queued for deployment.** One esbuild bundle, 1.83 MB, in a Node image with
`pg` and nothing else: no `node_modules`, no source tree, no npm at run time. `pg` stays external
because it resolves its own backend by require, and inlining that is how a bundled Postgres client fails
at connect instead of at build. The build refuses to ship an artifact containing a DSN, a key inside a
URL or an assigned secret — this service holds no keys, but it is built in a tree with `.env` files next
door and a credential baked into a layer outlives the process that used it.

The deployment task carries one instruction that matters more than the rest: **nothing that can sign may
go into its environment file**. No operator key, no keystore path, no password for one. The whole point
of the split is that this process cannot produce a signature, and an environment file is the one place
that could be undone by accident.

**4 Sep — D suggests, and refuses to guess.** `rank_pools` scores every pool a manager is configured
with by fee APR over the last complete day; `suggest_move` compares the position's pool against the rest
and returns the numbers for a move when the gap is worth it.

Two rules run through both. **Only the manager's own pools are candidates** — `moveLiquidity` can name a
pool only if the owner fixed it into the set at creation, so the candidates come from the manager on
chain rather than from a market-wide ranking that would look smarter and be useless. And **the output is
numbers, never calldata**: a pool id, two ticks and an amount, which the local server re-derives against
chain state and puts through the same policy and oracle guard as a hand-written call. A test asserts the
response contains nothing resembling a transaction.

It refuses in three places rather than guessing. A pool it could not score is listed separately with a
reason instead of being dropped or scored zero. One pool's failed lookup does not lose the rest of the
ranking. And when the *current* pool cannot be scored it holds — comparing against an assumed zero would
make every unmeasurable pool look worth leaving, which is exactly backwards.

Live against the Arbitrum manager it does precisely that: reads the four configured pools and the open
position, ranks none of them because that chain has no v4 analytics subgraph, and holds. Honest, and a
reminder for the demo — the ranking has data on Unichain and Base, not on Arbitrum.

Every suggestion carries the full ranking and five caveats, which are part of the answer rather than a
disclaimer: an agent reading one APR number will treat it as a forecast unless told that fees already
earned are realised by the move, that impermanent loss is not in the comparison, and that the default
range is a symmetric guess.

**4 Sep — D answers, over both surfaces.** The service exists as `insight/`, a second package beside the
local MCP server in the frontend repository, because it needs exactly the modules that server is
shedding. One process, two surfaces over the same functions: MCP over HTTP for an agent, REST for the
app. No key, no signer — by construction rather than by omission.

Verified live end to end, not just typechecked: `tools/list` returns both tools with their schemas, and
`tools/call` returns the same position we have been checking all evening — pool `0x70bf44c3…`, lifetime
fees 41 / 21904 across six events — with `source: "oracle"` and an empty degradation trail, because with
no database configured the index is left out of the cascade entirely rather than present-and-failing on
every request.

The cascade is the substance. Preference order is configuration; falling back is not — there is no
manual toggle, because a toggle gets set once and then never revisited while the index quietly falls
behind. Every answer carries which source served it, how current that source is, and why the ones ahead
of it did not. And the rule everything rests on: **an empty answer is an answer, an unavailable source is
not**. Collapsing those two is how an empty index looks broken and a broken one looks empty.

One consequence of that rule is worth stating because it is not obvious: the index **declines** for a
manager it has never seen, instead of reporting an empty history. For a manager it knows, no rows is a
real answer; for one it has never seen, ingestion not having reached the deployment is far more likely
than a manager that has done nothing in its life — and answering "no history" there would be a confident
lie.

A test caught a real ordering bug on the way: events were merged by timestamp, and a recenter shares both
block and timestamp with the fees it realises, so their order was undefined. Ordering is now by
`(block_number, log_index)`, which is the only total order there is — and the only one that exists at all
on the chains with no block-time feed.

Still to come here: `rank_pools` and `suggest_move`, then deployment behind Cloudflare.

**4 Sep — packaged and queued for the sink.** The package is published as a release
([v0.1.0](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/releases/tag/v0.1.0)), so the
sink takes a URL and the production host needs no Rust toolchain at all.

The quota decides the shape of the first load. A full Arbitrum backfill from the factory's block to the
chain head is 15.5M blocks against a 7M free tier, so the first run covers a **bounded window**,
486,400,000 → 487,600,000: the manager's creation, its first position, and the operator being appointed.
Roughly 1.2M blocks for the whole interesting stretch of history. Following the chain head on Arbitrum is
not affordable yet and the task says so rather than leaving it to be discovered when the key runs dry.

**4 Sep — B writes rows.** `db_out` emits `DatabaseChanges` for twelve tables, and the schema they land
in is defined and reviewed rather than whatever the sink happened to produce. Verified live on Arbitrum:
the row for block 486,482,005 carries the same pool, salt and ticks that `map_positions` produced, now in
the shape the sink applies. The database itself is up — a dedicated role and database on our existing
Postgres, four schemas, one per network, reachable only over the private network.

Two manifest lessons, both found by running rather than reading: importing the SQL protodefs package
alongside the database-changes one collides on `sf.substreams.sink.sql.v1.Service`, because the sink
Service type already lives inside the CLI; and changing `imports` invalidates cached module outputs,
because module hashes cover the package's proto definitions — a 338k-block store backfill ran a second
time to prove it.

**4 Sep — B runs against a live chain.** Toolchain in (rustc 1.98.1 + wasm32, substreams 1.22.0, protoc
36.1); the package builds, packs without warnings, and was run against Arbitrum One with a real key.

Both runs were cross-checked against the Envelop history API — the production indexer this package is
meant to eventually replace — on the same manager `0x60723973…264b`:

| Module | Block | Decoded |
|---|---:|---|
| `map_raw_events` | 487,466,603 | `OperatorSet`: operator `0xd5228c94…`, allowed |
| `map_positions` | 486,482,005 | first position: pool `0x70bf44c3…`, salt `0x8cd1b9d4…`, range `[58920, 70920]`, liquidity `+717932` |

Pool, salt and timestamp match the oracle's record of that position exactly, and the delta is positive
because it is an open. Worth noting what the two rows show together: the `emitter` of the position row is
the v4 `PoolManager` while the `manager` is the `sender` — which is the whole reason positions are read
from Uniswap's logs rather than from the manager's own events.

Added `index_events`, a block-index module emitting `evt:<name>` and `mgr:<address>`. Billing is per block
processed and these managers touch a tiny fraction of blocks, so this is the largest cost lever the
platform offers. Backfilling the store to the block above cost ~340k blocks of the 7M free tier, which
puts a number on why it matters. The manifest also gained a `networks` block, so one manifest covers
mainnet, arbitrum-one, base and unichain rather than four copies of it.

**4 Sep — B scaffolded.** Protobuf, ABIs, four modules and the manifest are in
[ethonline-2026-substreams-v4-lp](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp).
Nothing has been compiled yet — there is no Rust toolchain on the build machine — and the commit says so
rather than implying otherwise.

The design decision worth recording: the manager registry is built from the **factory's own deployment
event**, not from an address list, so the package works for any manager that factory produced on any
chain. That is also what lets `map_events` answer a question the pipeline it replaces cannot — whether the
contract that emitted a log is really one of ours. `OperatorSet(address,bool)` is a generic signature, and
the existing poller's event table has no address column, so a signature matches network-wide; hence its
explicit do-not-index list. Here it is one map step.

Positions come from Uniswap's `ModifyLiquidity` logs rather than the manager's own events, because the
manager's events cannot describe a position: `Allocated` carries a leg count, no manager event carries
amounts, and for the volatile product nothing on chain links a salt to its pool.

Next: toolchain, first build, then `db_out`, `graph_out` and a `blockIndex` module — the last is the
biggest cost lever there is, since billing is per block processed and managers are active in a tiny
fraction of them.

**4 Sep — A landed.** `moveLiquidity` implemented, 17 tests for it, 254 green overall.

Measured, from equal fresh state: one unlock **337,035** gas against **381,744 + 21,000** for
`withdrawTo` then `allocate` — about **66k saved**, and the idle window between the two transactions
gone. The first version of that benchmark ran both paths in one test and made the move look 37% *more*
expensive; whichever path goes second inherits the other's warm storage, which is worth more than the
difference being measured. Two tests from identical state, logging rather than asserting.

The EIP-170 budget decided the shape of the API, exactly as the plan warned it might. The array form —
many pulls, many adds — needs its own calldata-to-memory encoder and memory decoder for arrays of
structs, and that pair cost **947 bytes against 858 of headroom**. So the operation moves one position
to one destination; an operator repeats the call to move several. Cutting duplication paid for the rest:
`_allocateLegV` and `_rebalanceSwap` held the same five lines — swap, full-fill guard, minimum-out floor,
oracle check — and now share one `_guardedSwap`, which returned 233 bytes and leaves a single place where
those guards can drift. Final sizes: Volatile 24,432 (144 free), OpenVolatile 24,372 (204), Stable 24,178
(398).

Removing liquidity realises accrued fees, and only the claim path used to say so — which is why a
recenter or a withdrawal silently reset lifetime fee counters downstream. `_pullLiquidity` now emits the
same `FeesCollected` event with the same gross amounts, so every path that realises fees reports them and
no consumer has to change.

**4 Sep.** Plan published. Reconnaissance corrected three things we believed and would have got wrong:
the operation code we intended to use was already free under a different number than the docs claimed;
the branch we meant to build the fee-reporting event on turns out to contain no contract change at all,
so we introduce that event ourselves; and Chainlink has feeds on Arc mainnet but none on its testnet,
which decides where the operator loop gets demonstrated.
