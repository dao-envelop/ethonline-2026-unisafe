# Submissions — three tracks, what each asks for and what answers it

Written to be pasted. Each section has the track's hard requirements, whether we meet them and with
what evidence, the text for the form, and the things only a person can do.

Arc is not here. Its mainnet has no public RPC endpoint — the documentation still publishes testnet
only — and the owner postponed it rather than ship a deployment we could not demonstrate.

---

# Per-prize answers

Each prize form asks the same three things. Below is the text to paste, one block per sponsor.
**Every link is pinned to a commit**, so the line numbers cannot drift out from under a judge.

## Uniswap

**Why we qualify.** unisafe adds `moveLiquidity` — one operator call that closes a position in one
Uniswap v4 pool and opens it in another inside a **single `unlock`**, with one settlement pass and one
oracle-guarded swap: 337,035 gas against 381,744 + 21,000 for the withdraw-then-allocate path it
replaces, and no window where the capital sits idle. It is built straight on `PoolManager` — no
periphery `PositionManager`, no NFT per position — and we proved a multi-pool `unlock` against a bare
`PoolManager` before touching the manager.

**Live on chain.** Four operator `moveLiquidity` calls on Unichain, 10–11 September. In
[`0xc2a93eac…`](https://uniscan.xyz/tx/0xc2a93eac8fea442f8e022766dcd2b9d768ca9eed7504bc786c0d42c45014c888)
the v4 `PoolManager` emits `ModifyLiquidity` for **two different pools** inside one transaction —
liquidity out of `0xbd0f3a7c…`, into `0x51f9d63d…`, with the balancing swap between them. Full list with
mirrors: [README § Operator transactions](README.md#operator-transactions).

**Line of code.**
[`VolatileLPManager.sol#L407`](https://github.com/dao-envelop/uni-smart-wallet/blob/48006df4f28fbd9548e7e8600c782927954df7d0/src/VolatileLPManager.sol#L398-L410) — the one `POOL_MANAGER.unlock`
that carries both pools.
Supporting: [`CrossPoolUnlock.t.sol#L217`](https://github.com/dao-envelop/uni-smart-wallet/blob/48006df4f28fbd9548e7e8600c782927954df7d0/test/CrossPoolUnlock.t.sol#L217-L249) — the manager-free
proof, asserting one settlement pass over the currency union.

**Feedback.** v4 keys deltas by `(address, currency)`, not by pool — that is what makes a multi-pool
`unlock` legal, and it is the single fact this whole feature rests on, yet no page says it; the Batch
Modify guide asserts the conclusion without the mechanism, so we read `PoolManager._accountDelta` and
wrote our own test. Two more: contract size decided our API and there is no external library to push
plumbing into, and `POST /lp/pool_info` cannot answer "which v4 pools exist for this pair" — it refuses
with `V4 pools require fee and tick_spacing`. Full list: [`FEEDBACK.md`](https://github.com/dao-envelop/uni-smart-wallet/blob/48006df4f28fbd9548e7e8600c782927954df7d0/FEEDBACK.md).

## Chainlink

**Why we qualify.** An audit found that an operator could deploy principal at a distorted spot price
without swapping at all, so the guard was extended from swap prices to **every operator action** — adds
included — and now also bounds how far from the Chainlink reference an operator may park a range. The
on-chain state change is real: new `ChainlinkPriceOracle` contracts deployed and seeded with feeds on
five chains, with managers re-pointed at them by their owners.

**Live on chain.** Every operator call in
[README § Operator transactions](README.md#operator-transactions) passed this guard to land — the
`moveLiquidity` and `allocate` calls on Unichain through the new spot-and-midpoint branch, the Arbitrum
`recenter` calls through the swap branch. A refusal is not a log line, it is a revert, so a successful
operator transaction *is* the oracle's signature on it.

**Line of code.**
[`ChainlinkPriceOracle.sol#L317`](https://github.com/dao-envelop/uni-smart-wallet/blob/48006df4f28fbd9548e7e8600c782927954df7d0/src/oracle/ChainlinkPriceOracle.sol#L308-L318) — `checkOp`'s
zero-input branch: no swap to judge, so the pool's own price and the position's midpoint are judged
against the feed instead.
Supporting: [`BaseLPManager.sol#L377`](https://github.com/dao-envelop/uni-smart-wallet/blob/48006df4f28fbd9548e7e8600c782927954df7d0/src/BaseLPManager.sol#L370-L380) — the call site, which fails
closed when the oracle declines.

**Feedback.** Two things cost us time. Feed addresses are not published as a machine-readable per-chain
index, so a five-chain deploy script ends up carrying a hand-maintained JSON transcribed from the docs
site ([`script/oracle_feeds.json`](https://github.com/dao-envelop/uni-smart-wallet/blob/48006df4f28fbd9548e7e8600c782927954df7d0/script/oracle_feeds.json)) — a JSON endpoint keyed by chain id
and symbol would remove that whole class of transcription error. And the **L2 sequencer uptime feed** —
the thing that makes an L2 integration fail closed correctly — is documented away from the Price Feeds
quickstart, so it is easy to ship an L2 integration without learning it exists; worse, a chain that had
no uptime feed at deploy time can get one later and nothing tells you. Ours deployed on Unichain with
the gate off because there was no feed, and one has since been published
(`0x495639D9914e7D270c5dCC641BfB1d807423F813`) — we found it by re-reading the directory, not by being
told.

## The Graph

**Why we qualify.** Our Substreams package decodes a *class* of contracts rather than an address list —
the manager registry is built from the factory's own deployment event, so the factory address is the
only parameter — and it is itself **composed with a published package**, using `ethereum-common`'s
`index_events` as a block filter: 58,876 blocks in scope on mainnet, 1,149 actually processed. The index
it feeds is the first source behind both the dApp and a hosted MCP server that answers an agent's
questions, and every answer names the source that served it and how current that source is.

**Line of code.**
[`substreams.yaml#L55`](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/blob/30991427d38e59996ea1831d526a13b46f47b865/substreams.yaml#L52-L58) — the block filter: our package consuming another
published package's index, which is the composition itself.
Supporting: [`graphHistory.ts#L88`](https://gitlab.com/envelop/protocol-v2/stablelp-ui/-/blob/a170d94e09ccee4edede9a96d0f7b772a3cd98d1/insight/sources/graphHistory.ts#L84-L101) — the staleness
budget that makes an index safe to put in front of an agent: an index further behind head than its
budget declines and says so, instead of answering confidently with old data.

**Feedback.** Subgraph Studio no longer accepts substreams-powered subgraphs, and it fails *late*:
`graph build` succeeds, the IPFS upload succeeds, and the node refuses the deployment at the very end —
a deprecation notice at build time would have saved a day. Second: the sink's progress log counts blocks
in a way that does not match the Portal's billing counter — we sized a backfill from the log and were
off by an order of magnitude until we checked the Portal, so the log is easy to mistake for a cost
estimate.

---

## 1 · Uniswap — Best Stack Contribution (+ Continuity)

**What it asks**

| Requirement | Status |
|---|---|
| Public **GitHub** repository | ✅ [dao-envelop/uni-smart-wallet](https://github.com/dao-envelop/uni-smart-wallet), mirror in step with GitLab |
| `FEEDBACK.md` | ✅ [in the repo root](https://github.com/dao-envelop/uni-smart-wallet/blob/master/FEEDBACK.md) — seven items, all from this integration; [copy here](FEEDBACK.md) |
| Uniswap Developer Feedback Form linking to it | ✅ submitted by the owner, 13 Sep |
| README points at the contracts and lines | ✅ [README](https://github.com/dao-envelop/uni-smart-wallet#readme) names `src/VolatileLPManager.sol`, both tests and `FEEDBACK.md` |
| Continuity Track registration | ✅ done on the Hacker Dashboard, "Extend Open Source" |

**Short description (≤ 280 chars)**

> `moveLiquidity`: one operator call that pulls liquidity from one Uniswap v4 pool and adds it into
> another inside a single `unlock` — oracle-guarded, one settlement pass. It replaces
> withdraw-then-allocate: two transactions, two gas charges, and an idle window in between.

**What we built (long)**

> unisafe manages Uniswap v4 liquidity through a manager NFT. The owner may authorise operators — bots,
> agents — that can rebalance a position and can never withdraw; that boundary is in the contract.
>
> The gap we closed is what happens when a different pool becomes the better place to be. That was two
> transactions: `withdrawTo`, then `allocate`. Two intrinsic gas charges, two oracle checks at two
> different prices, and between them a window where the capital earns nothing.
>
> `moveLiquidity` does it in one. It is possible because v4 keys deltas by `(address, currency)` rather
> than by pool, and `unlock` checks exactly one thing on exit — that no non-zero delta remains. Nothing
> in v4 restricts a callback to a single pool; the documentation simply never says so, which is why we
> proved it with a standalone test against a bare `PoolManager` before touching the manager.
>
> Measured from equal fresh state: **337,035 gas** for the move against **381,744 + 21,000** for the
> two-call path — about 66,000 saved, and the idle window gone. The first version of that benchmark ran
> both paths in one test and made the move look 37% *more* expensive, because whichever path runs second
> inherits the other's warm storage; the number above comes from two tests from identical state.
>
> The shape of the API was decided by EIP-170, not by taste. The array form — many pulls, many adds —
> needs its own calldata-to-memory encoder and memory decoder for arrays of structs, and that pair cost
> 947 bytes against the 858 we had before the operation. So the operation moves one position to one destination, and cutting
> duplication paid for the rest: `allocate`, `recenter` and `move` now share one `_guardedSwap`, which
> returned 233 bytes and leaves a single place where those guards can drift.
>
> Deployed on Ethereum, Unichain, Base, Arbitrum and Unichain Sepolia on 8 September. Managers are
> EIP-1167 clones and are never migrated, so the operation reaches managers created from that release
> onward — we say so in the README and in the video rather than letting it be discovered.

**Where a judge should look**

- `src/VolatileLPManager.sol` — `moveLiquidity`, `_handleMove`, and `_guardedSwap`
- `test/CrossPoolUnlock.t.sol` — manager-free proof that v4 permits several pools in one `unlock`
- `test/VolatileLPManagerMove.t.sol` — 17 tests: behaviour, the oracle matrix, "nothing leaves the
  manager", and the gas benchmark
- `FEEDBACK.md` — what building this over v4 cost ([copy in this repo](FEEDBACK.md))

---

## 2 · The Graph — Composable/Standardized **and** AI Tooling (Continuity)

**What Composable asks**

| Requirement | Status |
|---|---|
| Composition of **≥ 2 Graph products** | ✅ our published Substreams package **plus** a published third-party package consumed as a dependency |
| **Live data** from a Graph provider | ✅ The Graph Market key against StreamingFast endpoints; SQL sink following Ethereum and Unichain heads |
| More than one query to one subgraph | ✅ eleven decoded event types, a position model, two sinks |
| Public repo + video 2–4 min | ✅ repo · ✅ [video](https://ethglobal.com/showcase/unisafe-xndpd) |

**What AI Tooling asks**

| Requirement | Status |
|---|---|
| Graph as a **load-bearing** part | ✅ the index is the first source for both the agent interface and the dApp |
| Live data only, no mocks | ✅ every number in the demo comes from the running sink or the chain |
| Reasoning, decisions, automation or an NL interface | ✅ `rank_pools` / `suggest_move` reason over indexed fees and propose a move an agent then executes |
| Pre-existing work documented | ✅ [README](README.md#what-existed-before-the-hackathon) and [AI_USAGE.md](AI_USAGE.md) |

**Short description (≤ 280 chars)**

> A Substreams package for the class "LP manager over Uniswap v4" — published, importable, and itself
> composed with a published package whose block index decides which blocks we open. It feeds a SQL
> index that answers an agent's questions and the dApp's alike.

**What we built (long)**

> The package decodes eleven event types of a *class* of contracts, not of our addresses: the manager
> registry is built from the factory's own deployment event, so pointing it at any deployment of the
> same factory on any chain fills the registry by itself. The factory address is the only parameter.
>
> Positions cannot be built from the managers' own events — `Allocated` carries a leg count, no manager
> event carries amounts, and for the volatile product nothing on chain links a position's salt to its
> pool — so the position model is built from Uniswap's `ModifyLiquidity` logs, where pool, range, signed
> liquidity delta and salt appear together. A recenter then decomposes for free into a negative row and
> a positive row under one salt.
>
> **The composition.** We import [`ethereum-common`](https://substreams.dev/packages/ethereum-common/v0.3.3)
> and use its `index_events` module as a block filter, so a block holding none of our signatures is
> never opened. Measured on mainnet: 58,876 blocks in scope, **1,149 processed**. Billing is per block
> processed, so this is not an optimisation — it is what makes the backfill affordable at all. Our own
> package is published in turn, as [`envelop-lp-v4`](https://substreams.dev/packages/envelop-lp-v4), so
> it can be imported the same way.
>
> **What we intended and could not do.** `graph_out` and a subgraph schema are written and verified
> against a live chain, but Subgraph Studio no longer accepts substreams-powered subgraphs — the build
> and the IPFS upload succeed and the node refuses the deployment outright. Both files stay in the
> package, and the README says so rather than leaving a reader to find out at deploy time.
>
> **What the index is for.** A hosted MCP server answers an agent's questions from it — position history
> and realised fees, who may operate a manager, which of its pools pays best over the last complete day,
> whether moving a position is worth it — and the dApp reads the same service, so the app and the agent
> cannot disagree. Every answer names the source that served it and how current that source is.
>
> That last part was earned rather than designed in. On 10 September the sink stopped: a provider's
> authentication service began refusing every stream. The service kept answering from an index an hour
> behind, and the failure surfaced when the owner noticed that a fee claim he had just made was missing.
> The cascade now declines an index further behind head than its budget, says so in the answer, and a
> watchdog restarts a stalled sink and escalates only when restarting does not help.

**Where a judge should look**

- [`src/lib.rs`](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/blob/master/src/lib.rs) —
  the modules; the registry is built from the factory's event
- [`substreams.yaml`](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/blob/master/substreams.yaml) —
  the `ethereum-common` import and the block filter, with the numbers in the comment
- [`insight/sources/`](https://github.com/dao-envelop/ethonline-2026-frontend-mirror/tree/master/insight/sources) —
  the cascade: index, oracle, log scan, and the staleness rule
- `https://unisafe.envelop.is/mcp` — the running server; `/healthz` shows per-chain index lag

---

## 3 · Chainlink — Powered Upgrade (Continuity)

**What it asks**

| Requirement | Status |
|---|---|
| Improve an existing project using **Price Feeds** | ✅ the operator guard was extended from swaps to liquidity adds |
| **On-chain state change** (mandatory) | ✅ a new `ChainlinkPriceOracle` deployed on five chains on 8 Sep and seeded with feeds; managers point at it via `setPriceOracle` |
| Continuity registration | ✅ done |

**Short description (≤ 280 chars)**

> An audit found that an operator could deploy principal at a distorted spot price without swapping at
> all. The fix runs every operator action past a Chainlink feed — not just swaps — and bounds where an
> operator may park a range relative to the reference.

**What we built (long)**

> unisafe already used Chainlink Price Feeds to vouch for the *execution price* of a swap an operator
> triggered. An audit on 4 September found the hole that leaves: an operator could add liquidity without
> swapping, at whatever the pool's spot price happened to be, and place principal at a distorted price —
> measured at −22.4% and −44.5% of a portfolio in a single call.
>
> Three changes, all deployed:
>
> 1. **Every operator action is checked, not only swaps.** `ChainlinkPriceOracle` gained a spot branch:
>    `check` with `amountIn == 0` compares the pool's `slot0` against the Chainlink reference in both
>    directions, within its own tolerance. `allocate`, `allocateFrom`, `reinvest`, `recenter` and
>    `moveLiquidity` all pass through it, and fail closed when no feed is configured.
> 2. **Where an operator may park liquidity is bounded by the reference.** A range's midpoint must sit
>    within θ of the Chainlink price. The loss from a parked range *is* its distance from fair value, so
>    that distance is the accepted cost per operation — and no pool is closed by it: a narrow range at a
>    fair price is legal at any tick spacing.
> 3. **One operator action per transaction**, so a batch cannot walk the pool between checks.
>
> The on-chain state change is a deployment, not a demo: new oracle contracts on Ethereum, Unichain,
> Base, Arbitrum and Unichain Sepolia, seeded with feeds for every currency each chain has one for, and
> managers re-pointed at them by their owners.
>
> The frontend was taught the same vocabulary, because a guard nobody can see is a guard that surprises
> people: the manager screen shows all three tolerances, an operator's default range is centred on the
> Chainlink reference rather than on the pool, the balancing swap is capped so an operation cannot trip
> its own spot check, and each refusal has copy that says which bound was crossed and what to do.

**Where a judge should look**

- `src/oracle/ChainlinkPriceOracle.sol` — the feed registry, the swap branch and the new spot branch
- `src/BaseLPManager.sol` — `_guardSwap` / the add-side guard, and `MAX_OPS_PER_TX`
- `script/SetOracleFeeds.s.sol` — what was written on chain
- `stablelp-ui`: `src/components/manager/OracleSection.tsx`, `src/lib/oracleReference.ts`

---

## Artwork

Both images the submission form asks for are in [`brand/`](brand/): `logo-512.png` (square) and
`cover-1280x720.png` (16:9, with `cover-640x360.png` as the small variant). Same mark, palette and type
as the product itself.

## What only a person can do

**Submitted:** [unisafe-xndpd](https://ethglobal.com/showcase/unisafe-xndpd). The project page is live and the demo video plays on it.

1. ✅ **The demo video** — recorded, cut and published with the submission. Narration timed per segment
   in [demo/VOICEOVER.md](demo/VOICEOVER.md), end cards in [demo/slides/](demo/slides/).
2. ✅ **Submit on ETHGlobal** — done, inside the deadline.
3. ✅ **Uniswap Developer Feedback Form** — filled in and sent, with the link to
   [`FEEDBACK.md`](FEEDBACK.md).
4. ✅ **Continuity Track registration** — "Extend Open Source", confirmed by the owner.

Nothing is outstanding.

## Facts worth keeping straight in every form

- Managers are non-upgradeable clones: `moveLiquidity` reaches managers created from the 8 September
  release onward, not the ones already live.
- The index follows Ethereum and Unichain. Arbitrum stays on Envelop's own indexer, because per-block
  billing and quarter-second blocks are bad arithmetic.
- Ranking is fee APR over the last complete day. It is not a forecast, and impermanent loss is not in it.
- Roughly 24k lines of audited contracts predate the event. What was built during it is listed in the
  [README](README.md#what-we-are-building-during-the-event); everything else is stated as prior work.
