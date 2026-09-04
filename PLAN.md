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
| A — `moveLiquidity` | ✅ implemented | `5a77c41` → `cc7d732` on `task/051-cross-pool-move` |
| B — Substreams package | 🟡 builds, runs live, verified against the oracle | `1803105` → `55fa54c` |
| C — local MCP slimmed | ⬜ not started | — |
| D — hosted service | ⬜ not started | — |
| E — Arc deployment | ⬜ not started | — |
| Demo video | ⬜ not started | — |

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
