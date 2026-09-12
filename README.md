# unisafe — ETHOnline 2026

**Move liquidity between Uniswap v4 pools in a single transaction, and let an agent decide when to.**

🏆 **[Submitted on ETHGlobal](https://ethglobal.com/showcase/unisafe-xndpd)** — project page, with the demo video.
📊 **[The pitch deck](https://dao-envelop.github.io/ethonline-2026-unisafe/)** — eight slides and the two cards that close the video. Source in [`docs/`](docs/).

This is the submission hub for [unisafe.envelop.is](https://unisafe.envelop.is) at ETHOnline 2026.
The code lives in the repositories linked below; this page tells you what we built during the event,
where to look, and how to run it.

Submitted under the **Continuity** track (*Extend Open Source*). Everything listed under
[What existed before](#what-existed-before-the-hackathon) predates the event and is not part of what
we are asking to be judged.

---

## The problem

unisafe manages Uniswap v4 liquidity through a **manager NFT**. Whoever holds the NFT owns the funds;
they may authorise **operators** — bots, agents, other people — who can rebalance the position but can
never withdraw. That boundary is enforced by the contract, not by trust: operator swaps are additionally
gated by a Chainlink price oracle, and there is no code path from an operator to the owner's principal.

The gap is what happens when a *different pool* becomes the better place to be. Today an operator has to:

1. `withdrawTo` — close the position and pull the capital back to the manager,
2. `allocate` — open a new position somewhere else.

Two transactions. Two intrinsic gas charges, two settlement passes, two separate oracle checks at two
different prices — and, between them, **a window where the capital sits idle**, earning nothing, while
the manager looks from the outside like the operator broke something.

The manager already has an operation that does remove → swap → re-add atomically (`recenter`), but it is
locked to a single pool.

## What we are building

**`moveLiquidity`** — one operator call that pulls liquidity from one or more pools and adds it to others
inside a single Uniswap v4 `unlock`, with one settlement pass and one oracle-guarded swap path.

This is possible because v4 keys deltas by `(address, currency)` rather than by pool, and `unlock`
checks exactly one thing on exit — that no non-zero delta remains. Nothing in v4 restricts a callback to
a single pool; the documentation simply never says so. We proved it with a standalone test before
touching the manager.

Around that, three supporting pieces:

- a **Substreams package** that decodes LP-manager events into typed protobuf, so positions, realised
  fees and operator changes are queryable without a full log scan;
- a **split of our MCP server** into a thin local signer and a hosted read/strategy service, so the
  component holding the operator key does nothing but build, check and sign transactions;
- a **deployment on Arc**, Circle's stablecoin-native L1, where USDC is the gas token.

**The end-to-end scenario, which is also the demo:** the hosted service ranks v4 pools by yield from
indexed data, proposes a better one, the local MCP server builds `moveLiquidity`, checks it against its
policy and simulates it — and one transaction moves the liquidity, with every swap inside it verified
against a Chainlink feed.

## How it fits together

```mermaid
flowchart LR
  subgraph chain["Chain — Ethereum · Unichain · Base · Arbitrum · Unichain Sepolia"]
    MGR["StableLPManager / VolatileLPManager<br/>EIP-1167 clones, owner holds the NFT"]
    V4["Uniswap v4 PoolManager"]
    ORC["ChainlinkPriceOracle<br/>gates every operator swap and add"]
    MGR -->|unlock, modifyLiquidity, swap| V4
    MGR -->|check| ORC
  end

  subgraph local["Operator's machine"]
    MCP["envelop-mcp-lp (local)<br/>holds the key · builds calldata<br/>policy · simulate · sign<br/>no outbound HTTP except RPC"]
  end

  subgraph hosted["unisafe.envelop.is"]
    INS["lp-insight (hosted MCP + REST)<br/>history · yield · rank_pools · suggest_move<br/>no key, cannot sign"]
    APP["The dApp"]
  end

  subgraph graph["The Graph"]
    SUB["Substreams package<br/>map_events · map_positions"]
    DB[("Postgres index<br/>db_out")]
    SG["Substreams-powered subgraph<br/>graph_out"]
    SUB --> DB
    SUB --> SG
  end

  ORACLE["Envelop oracle API<br/>fallback source"]

  V4 -.->|logs| SUB
  MGR -.->|logs| SUB
  DB --> INS
  ORACLE -.->|when the index is behind or blind| INS
  INS -->|numbers: pool id, ticks, amounts<br/>never calldata| MCP
  MCP -->|one transaction: moveLiquidity| MGR
  APP --> INS
```

The arrow that matters is the one from the hosted service to the local one: it carries **numbers, not
calldata**. A pool id, two ticks and an amount, which the local server re-derives against chain state and
puts through the same policy and oracle guard as a hand-written call. The component that can sign cannot
be handed something to sign.

---

## Repositories

| Repository | What is in it |
|---|---|
| [dao-envelop/uni-smart-wallet](https://github.com/dao-envelop/uni-smart-wallet) | Solidity contracts. `StableLPManager`, `VolatileLPManager`, `OpenVolatileLPManager`, the factory, `UniLens`, `ChainlinkPriceOracle`. **`moveLiquidity` lands here.** |
| [dao-envelop/ethonline-2026-substreams-v4-lp](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp) | Substreams package for the LP-manager event class. |
| [gitlab.com/envelop/protocol-v2/stablelp-ui](https://gitlab.com/envelop/protocol-v2/stablelp-ui) | The dApp and both MCP servers — the local signer (`mcp/`) and the hosted read/strategy service (`insight/`). Public, and canonical: this is where it is developed. |
| [dao-envelop/ethonline-2026-frontend-mirror](https://github.com/dao-envelop/ethonline-2026-frontend-mirror) | **GitHub mirror of the above**, full history, for anyone who would rather read it here. Pushed from the same `master`. |
| [gitlab.com/envelop/protocol-v2](https://gitlab.com/envelop/protocol-v2) | Upstream home of the contracts and the frontend. Both public. |

> Specific file-and-line pointers for each track are in [Where to look](#where-to-look), so you do not
> have to go hunting.

---

## What existed before the hackathon

Stated plainly, because the Continuity track asks for it and because ~24k lines of audited contracts
should not look like a week's work.

- **The manager contracts**, live and non-upgradeable, deployed on Ethereum, Unichain, Unichain Sepolia,
  Base and Arbitrum. Three products: `StableLPManager` (oracle type 3000), `VolatileLPManager` (3001),
  `OpenVolatileLPManager` (3002, pools with hooks). Deployed instances are EIP-1167 clones.
- **The operator model**: owner-held singleton NFT, `setOperator`, and a contract-level guarantee that an
  operator cannot reach the principal. Operator swaps are checked against `ChainlinkPriceOracle` and fail
  closed when no feed is configured.
- **`recenter`** — atomic remove → swap → re-add, within one pool. `moveLiquidity` is its cross-pool
  generalisation.
- **The dApp** at unisafe.envelop.is — creating managers, allocating, recentering, position charts.
- **`@envelop/mcp-lp`** — a local MCP server giving an LLM agent the operator role, with a propose →
  simulate → execute loop, a default-deny policy guard and an encrypted keystore. Running against a real
  Arbitrum manager since July 2026.
- **An event indexer** (Envelop oracle) covering five chains, serving position history to the frontend.

## What we are building during the event

| # | Workstream | Repository |
|---|---|---|
| A | `moveLiquidity` — cross-pool move in one `unlock`, oracle-guarded, reporting realised fees | uni-smart-wallet |
| B | Substreams package over the manager's events + SQL sink | substreams-uniswap-v4-lp |
| C | Local MCP reduced to key, calldata, policy and broadcast; gains `propose_move` / `execute_move` | unisafe |
| D | Hosted read/strategy MCP over HTTP: history, yield, pool ranking, `suggest_move` | unisafe |
| E | Deployment on Arc (chain 5042) with Chainlink feeds and a USDC/EURC pool | uni-smart-wallet |
| F | The operator price guard extended from swaps to **every** operator action, plus a bound on where a range may sit and one operator call per transaction | uni-smart-wallet |

The split in C and D is the point, not an implementation detail. The component that holds the operator
key ends up with **no outbound HTTP at all except RPC**. The hosted service can suggest a move; it can
never produce a signature, and everything it suggests is re-derived and re-checked locally before
anything is signed.

---

## Where to look

*Filled in as each piece lands — see [Status](#status).*

**Uniswap** — the new operation and the test that justifies it, on `master` and deployed on all five chains:
- [`src/VolatileLPManager.sol`](https://github.com/dao-envelop/uni-smart-wallet/blob/master/src/VolatileLPManager.sol)
  — `moveLiquidity`, its `_handleMove` handler, and `_guardedSwap`, the one swap path allocate, recenter
  and move all share
- [`test/CrossPoolUnlock.t.sol`](https://github.com/dao-envelop/uni-smart-wallet/blob/master/test/CrossPoolUnlock.t.sol)
  — manager-free proof that v4 permits several pools in one `unlock`, written before the manager was touched
- [`test/VolatileLPManagerMove.t.sol`](https://github.com/dao-envelop/uni-smart-wallet/blob/master/test/VolatileLPManagerMove.t.sol)
  — 17 tests: behaviour, the oracle matrix, the "nothing leaves the manager" check, and the gas benchmark
- [`FEEDBACK.md`](https://github.com/dao-envelop/uni-smart-wallet/blob/master/FEEDBACK.md) — the seven things that cost us time building over v4
  ([same file in this repo](FEEDBACK.md), if you would rather not leave the hub)

**The Graph** — the package and what consumes it:
- [`proto/envelop/lp/v1/lp.proto`](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/blob/master/proto/envelop/lp/v1/lp.proto)
  — one message type per event, amounts as base-unit decimal strings
- [`src/lib.rs`](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/blob/master/src/lib.rs)
  — the four modules; the registry is built from the factory's deployment event, not an address list
- [`substreams.yaml`](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/blob/master/substreams.yaml)
  — factory address as the only parameter, per-chain table in that repo's README
- the package is **published to the registry**: [`envelop-lp-v4`](https://substreams.dev/packages/envelop-lp-v4),
  so anyone can import it the way we import someone else's
- **composition with a published package**: `substreams.yaml` imports
  [`ethereum-common`](https://substreams.dev/packages/ethereum-common/v0.3.3) and uses its `index_events`
  as a block filter, so a block holding none of our eleven signatures is never opened. Measured on
  mainnet: 58,876 blocks in scope, 1,149 processed
- [`schema.graphql`](https://github.com/dao-envelop/ethonline-2026-substreams-v4-lp/blob/master/schema.graphql)
  and `graph_out` — written and verified on Unichain, but **Subgraph Studio no longer accepts
  substreams-powered subgraphs** (its words: "no longer supported"), which is why the second Graph
  product here is the published package and the composition rather than a hosted subgraph
- verified against Arbitrum One and cross-checked with the production oracle, and `graph_out` verified on
  Unichain (manager creation at 54,551,071, first allocate at 54,572,737) — see that repo's README
- the hosted service reads the index live at `unisafe.envelop.is/mcp`, with the fallback cascade below

**Chainlink** — price feeds gating operator swaps:
- [`src/oracle/ChainlinkPriceOracle.sol`](https://github.com/dao-envelop/uni-smart-wallet/blob/master/src/oracle/ChainlinkPriceOracle.sol)
  and `_guardSwap` in [`src/BaseLPManager.sol`](https://github.com/dao-envelop/uni-smart-wallet/blob/master/src/BaseLPManager.sol)
- the on-chain state change: a new `ChainlinkPriceOracle` deployed on all five chains on 8 September and
  seeded with feeds, plus the spot branch added during the event — `check` with `amountIn == 0` compares
  the pool's `slot0` against the Chainlink reference in both directions, which is what now gates an
  operator's liquidity adds and not only its swaps
- feed wiring on Arc _(pending — Arc mainnet has 30 feeds; see [Status](#status))_

**Arc** — deployment and addresses _(pending)_

**Storage** — [`db/`](db/): what the Substreams SQL sink writes and why it is shaped that way. Twelve
tables — eleven event types plus `position_delta`, the one that actually models a position.

## Status

| | | |
|---|---|---|
| A | `moveLiquidity` | ✅ implemented, deployed on all five chains 8 Sep (release 2.1.0), and in the dApp — an owner can move a position between pools, not only an agent |
| B | Substreams package | ✅ published on [substreams.dev](https://substreams.dev/packages/envelop-lp-v4); SQL sink live on Ethereum and Unichain; composed with a published third-party package. Subgraph Studio no longer accepts substreams-powered subgraphs — see below |
| C | Local MCP slimmed + `move` | ✅ published — `@envelop/mcp-lp`, now 1.2.0: two bugs that broke a cross-pool move were found on a live manager after 1.0.0 and fixed in 1.1.0 and 1.2.0 |
| D | Hosted read/strategy MCP | ✅ live at `unisafe.envelop.is/mcp`, and the dApp reads it first: index → oracle → chain, with the source named on screen |
| E | Arc deployment | ⬜ out of this submission — Arc mainnet has no public RPC and the owner postponed it |
| F | Operator guard extended | ✅ audit 2026-09-04 [H-1] closed; new `ChainlinkPriceOracle` deployed and seeded on five chains 8 Sep, managers re-pointed by their owners |
| — | Demo video | ✅ recorded, cut and [published with the submission](https://ethglobal.com/showcase/unisafe-xndpd); script, shot list and end cards in [demo/](demo/) |

Submitting to three tracks: **Uniswap**, **The Graph** and **Chainlink**. Arc is not among them.

Event runs 4–13 September 2026. The full plan, the reasoning behind each decision and a dated progress
log are in **[PLAN.md](PLAN.md)** — published before the work, and corrected in place when reality
disagrees with it.

## Demo

**[The submission on ETHGlobal](https://ethglobal.com/showcase/unisafe-xndpd)** — the demo video plays there.
The two cards that close it are the last slides of [the deck](https://dao-envelop.github.io/ethonline-2026-unisafe/).

## Operator transactions

Every call below was sent by the **operator** account `0xD5228C948036eBe777b95f0124548882cbEF05d2` —
the one the local MCP server signs with. It has never been able to withdraw: there is no code path from
an operator to the principal, and each of these calls also had to pass the Chainlink guard.

Links go to the canonical explorer, with a Blockscout mirror (`bs`) beside each for anyone the
Etherscan family blocks.

### Unichain · manager [`0x7C77e35F…`](https://unisafe.envelop.is/manager/130/0x7c77e35faed086b948e68cd2ab534991995c3b3b)

| When (UTC) | Call | Transaction |
|---|---|---|
| 11 Sep 09:35 | `moveLiquidity` | [0xc2a93eac…14c888](https://uniscan.xyz/tx/0xc2a93eac8fea442f8e022766dcd2b9d768ca9eed7504bc786c0d42c45014c888) · [bs](https://unichain.blockscout.com/tx/0xc2a93eac8fea442f8e022766dcd2b9d768ca9eed7504bc786c0d42c45014c888) |
| 11 Sep 05:49 | `moveLiquidity` | [0x89dabe6c…1b5d32](https://uniscan.xyz/tx/0x89dabe6c84f484446a5d4a887153e36412169c9c34adce92c9eaaede971b5d32) · [bs](https://unichain.blockscout.com/tx/0x89dabe6c84f484446a5d4a887153e36412169c9c34adce92c9eaaede971b5d32) |
| 11 Sep 05:48 | `moveLiquidity` | [0x0169b6cd…642c95](https://uniscan.xyz/tx/0x0169b6cdd634820d151df4292c65f50a1a76c90d7020b2ddbc0dd437a6642c95) · [bs](https://unichain.blockscout.com/tx/0x0169b6cdd634820d151df4292c65f50a1a76c90d7020b2ddbc0dd437a6642c95) |
| 11 Sep 05:36 | `moveLiquidity` | [0xf95b1775…79f5d4](https://uniscan.xyz/tx/0xf95b17758f7aed13ce3bd85f6b3c9ad620c1c48da4745d118011a7352979f5d4) · [bs](https://unichain.blockscout.com/tx/0xf95b17758f7aed13ce3bd85f6b3c9ad620c1c48da4745d118011a7352979f5d4) |
| 11 Sep 05:49 | `allocate` | [0xf918c5fd…bd2fc2](https://uniscan.xyz/tx/0xf918c5fde5e518c74f71a55f56aad890ba733d2a5ebe8d89e32ab7f738bd2fc2) · [bs](https://unichain.blockscout.com/tx/0xf918c5fde5e518c74f71a55f56aad890ba733d2a5ebe8d89e32ab7f738bd2fc2) |
| 10 Sep 11:07 | `claimFees` | [0x53f1b40d…f05abd](https://uniscan.xyz/tx/0x53f1b40ddd36c529608b233bfea5daa5f5061187d999ec035b215a1b38f05abd) · [bs](https://unichain.blockscout.com/tx/0x53f1b40ddd36c529608b233bfea5daa5f5061187d999ec035b215a1b38f05abd) |
| 10 Sep 11:06 | `claimFees` | [0xf8846d82…b948d2](https://uniscan.xyz/tx/0xf8846d825594f2d28db6bfa6acd5ba48af1b1f8b2b1d14cc1ea1b96b68b948d2) · [bs](https://unichain.blockscout.com/tx/0xf8846d825594f2d28db6bfa6acd5ba48af1b1f8b2b1d14cc1ea1b96b68b948d2) |

**What one `moveLiquidity` looks like on chain** — [`0xc2a93eac…`](https://uniscan.xyz/tx/0xc2a93eac8fea442f8e022766dcd2b9d768ca9eed7504bc786c0d42c45014c888), block 58,370,992,
560,640 gas, **one transaction**:

- two `ModifyLiquidity` events from the v4 `PoolManager` (`0x1F98…0004`) in **two different pools** —
  `−1,446,934` liquidity out of pool `0xbd0f3a7c…`, `+13,713,827,842` into pool `0x51f9d63d…`
- one `Swap`, in the destination pool, because the two pools are two different pairs
- `FeesCollected` and `ProtocolFeeTaken` — the fees the removal realised, reported rather than swallowed
- `LiquidityMoved`, then `MetadataUpdate`, so the NFT's rendered state follows in the same transaction

That is the whole claim, visible in one receipt: several pools inside one `unlock`, one settlement pass.

> The 337,035 gas quoted elsewhere is the benchmark — the move against withdraw-then-allocate from
> **equal fresh state, same pair, no intermediate swap**. This live one costs more because it crosses
> two different pairs (so it swaps) and runs on cold storage. Both numbers are real; they answer
> different questions, and neither is the other's correction.

### Arbitrum

| When (UTC) | Call | Transaction | Manager |
|---|---|---|---|
| 10 Sep 11:03 | `allocate` | [0xab699054…183d02](https://arbiscan.io/tx/0xab69905460353eed95843c738a6bd2a16b689deb627d38002bdfcb19f3183d02) · [bs](https://arbitrum.blockscout.com/tx/0xab69905460353eed95843c738a6bd2a16b689deb627d38002bdfcb19f3183d02) | 0xCD302d06… |
| 25 Aug 02:47 | `recenter` | [0xf3c9a118…069447](https://arbiscan.io/tx/0xf3c9a1181c38887bc0e120b25145fe01c4df23b308fcc1a652f71d0ad3069447) · [bs](https://arbitrum.blockscout.com/tx/0xf3c9a1181c38887bc0e120b25145fe01c4df23b308fcc1a652f71d0ad3069447) | 0x60723973… |
| 22 Aug 02:09 | `recenter` | [0x5647699a…16668f](https://arbiscan.io/tx/0x5647699acfd84c2d86ad6bff101a08d3f8c97d1de592ed32cb6a886a2016668f) · [bs](https://arbitrum.blockscout.com/tx/0x5647699acfd84c2d86ad6bff101a08d3f8c97d1de592ed32cb6a886a2016668f) | 0x60723973… |
| 21 Aug 09:47 | `recenter` | [0x14c74b26…53b2de](https://arbiscan.io/tx/0x14c74b261e4cff262d282bf964793747271d41ebea635abb01f9f8c68553b2de) · [bs](https://arbitrum.blockscout.com/tx/0x14c74b261e4cff262d282bf964793747271d41ebea635abb01f9f8c68553b2de) | 0x60723973… |
| 21 Aug 01:47 | `recenter` | [0x52dab1cb…10e6c0](https://arbiscan.io/tx/0x52dab1cb7a8982908b45f566624339e99503b41d55d26bef08c6fdccd510e6c0) · [bs](https://arbitrum.blockscout.com/tx/0x52dab1cb7a8982908b45f566624339e99503b41d55d26bef08c6fdccd510e6c0) | 0x60723973… |
| 20 Aug 09:18 | `recenter` | [0xb6add35d…d1c429](https://arbiscan.io/tx/0xb6add35d1ec498f4762ecdd19a662e8c3cd0018e357372cb90c6ad9644d1c429) · [bs](https://arbitrum.blockscout.com/tx/0xb6add35d1ec498f4762ecdd19a662e8c3cd0018e357372cb90c6ad9644d1c429) | 0x60723973… |
| 20 Aug 01:57 | `recenter` | [0x61a08d03…90b5ab](https://arbiscan.io/tx/0x61a08d03643b40972157ad875c958730557ce092412cfef172c175344190b5ab) · [bs](https://arbitrum.blockscout.com/tx/0x61a08d03643b40972157ad875c958730557ce092412cfef172c175344190b5ab) | 0x60723973… |
| 20 Aug 01:56 | `recenter` | [0x60a14159…1e39e7](https://arbiscan.io/tx/0x60a14159681a306c7993b6ad18229a12284e905bb34f97290d4fd425a11e39e7) · [bs](https://arbitrum.blockscout.com/tx/0x60a14159681a306c7993b6ad18229a12284e905bb34f97290d4fd425a11e39e7) | 0x60723973… |
| 25 Jul 06:24 | `recenter` | [0x8cea5486…b5af05](https://arbiscan.io/tx/0x8cea54861633a1f0be8b44b63cb96dbaa530239e5cb940e8d7aefb80d9b5af05) · [bs](https://arbitrum.blockscout.com/tx/0x8cea54861633a1f0be8b44b63cb96dbaa530239e5cb940e8d7aefb80d9b5af05) | 0x60723973… |

The `recenter` calls from 25 July onward are the operator loop that predates the hackathon, listed under
[what existed before](#what-existed-before-the-hackathon) — the same key, the same server, before any of
this event's work existed. `moveLiquidity` does not appear here: Arbitrum's managers were created before
the 2.1.0 release, and managers are non-upgradeable clones.


What is ready: the [shot list](demo/SCRIPT.md), the [narration script](demo/VOICEOVER.md) timed segment by segment, and two [end cards](demo/slides/) with their own [voice-over](demo/slides/VOICEOVER.md). Submission artwork — square logo and 16:9 cover — is in [brand/](brand/).

---

## Rules and disclosure

- **Continuity.** Submitted under *Extend Open Source*. Pre-existing work is listed above; only work done
  between 4 and 13 September 2026 is offered for judging.
- **History.** Work is committed incrementally as it happens, in the repositories linked above. No squashed
  dumps.
- **AI usage.** Disclosed in **[AI_USAGE.md](AI_USAGE.md)**, including what the tooling did, what it did
  not decide, and where it was wrong.
- **Dependencies.** Open-source and named: Uniswap v4 core and periphery, OpenZeppelin, Foundry, the
  Substreams SDKs, viem, Next.js.
- [ETHGlobal rules and code of conduct](https://ethglobal.com/rules).

## Links

- Track submissions, requirement by requirement — [SUBMISSIONS.md](SUBMISSIONS.md)
- Live app — https://unisafe.envelop.is
- Plan and progress log — [PLAN.md](PLAN.md)
- Contracts — https://github.com/dao-envelop/uni-smart-wallet
- Envelop — https://envelop.is

## License

MIT, matching the repositories it links to.
