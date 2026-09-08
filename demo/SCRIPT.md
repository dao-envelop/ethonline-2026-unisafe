# Demo video — script and shot list

**Draft.** The chain the live transaction runs on is not settled yet; everything below assumes Unichain,
where both new implementations are allowlisted in the factory and the new oracle is already seeded with
feeds. Swap the chain and the addresses change, nothing else.

Target length **2:40–3:20** (the tracks ask for 2–4 minutes). One take per section, screen capture with
voice-over. No music under the terminal sections — the numbers are the point.

---

## 0:00 – 0:25 · The gap, stated once

**On screen:** the manager page at unisafe.envelop.is, one open position, in range.

> A manager NFT owns Uniswap v4 liquidity. Whoever holds the NFT owns the funds, and can authorise an
> operator — a bot, an agent — that may rebalance the position and can never withdraw it. That boundary is
> in the contract, not in a promise.
>
> The gap is what happens when a different pool becomes the better place to be. Today that is two
> transactions: close here, open there. Two gas charges, two oracle checks at two different prices, and
> between them a window where the capital earns nothing.

**Cut to:** the two-transaction path in the UI, briefly, then stop.

---

## 0:25 – 1:00 · What we built, in one sentence each

**On screen:** the architecture diagram from the README, then the four repos.

> `moveLiquidity`: one operator call that pulls liquidity out of one pool and adds it into another
> inside a single Uniswap v4 `unlock`. It is possible because v4 keys deltas by address and currency
> rather than by pool, and `unlock` checks exactly one thing on exit — that no non-zero delta remains.
> Nothing in v4 forbids several pools in one callback; the documentation simply never says so. We proved
> it with a standalone test before touching the manager.
>
> Around it: a Substreams package that decodes the manager's events, feeding both a SQL index and a
> subgraph; and a split of our MCP server into a hosted half that reads and reasons, and a local half
> that holds the key.

---

## 1:00 – 1:45 · The Graph side, live

**On screen:** terminal. `substreams run … graph_out` against Unichain, showing entities appearing.
Then the subgraph in Studio answering a query for the same manager.

> One decoder, two Graph products. The SQL sink writes the eleven event tables our production schema
> already has, so its rows can be compared row by row against the indexer it replaces. The subgraph gets
> a model instead: managers, operators already folded into "who may act now", positions with running
> liquidity and lifetime fees, and one timeline of everything a manager ever did.
>
> Positions come from Uniswap's own `ModifyLiquidity` logs, not from the manager's events — because the
> manager's events cannot describe a position. `Allocated` carries a leg count, no event carries amounts,
> and for the volatile product nothing on chain links a position's salt to its pool.

**Show:** the same position from both sources agreeing.

---

## 1:45 – 2:40 · The move itself

**On screen:** an agent session against the hosted server, then the local one.

> The hosted service ranks the manager's own pools by fee APR — its own pools, because `moveLiquidity`
> can only name a pool the owner fixed into the set when the manager was created. It refuses to guess:
> a pool it cannot score is listed with a reason rather than scored zero, and when the *current* pool
> cannot be scored it holds, because comparing against an assumed zero would make every unmeasurable
> pool look worth leaving.
>
> What it returns is numbers — a pool id, two ticks, an amount. Never calldata. The local server
> re-derives that against chain state, puts it through the same policy and the same oracle guard as a
> hand-written call, simulates it, and only then signs.

**Then:** `execute_move`, the transaction hash, the explorer.

> One transaction. 337,035 gas against 381,744 plus a second 21,000 for the two-call path — about 66,000
> saved, and the idle window gone. Every swap inside it verified against a Chainlink feed, and the
> operator still cannot reach the principal.

---

## 2:40 – 3:05 · What this does not do

Say it plainly; it is short, and it is what makes the rest credible.

> Managers are non-upgradeable clones. Every manager that existed before this deployment keeps the
> implementation it was created from, so `moveLiquidity` reaches managers created from today onward — not
> the ones already live.
>
> The index follows Ethereum and Unichain. Arbitrum stays on our own oracle, because a per-block quota
> and quarter-second blocks are bad arithmetic, and pretending otherwise would just be a bill.

---

## 3:05 – 3:20 · Close

**On screen:** the submission hub README.

> Contracts, the Substreams package, both MCP servers and the app are open, linked from one page, with
> file-and-line pointers for each track. `FEEDBACK.md` says what building this over v4 actually cost.

---

## Shot checklist

- [ ] Manager page with a live position (in range, real numbers)
- [ ] `test/CrossPoolUnlock.t.sol` on screen for two seconds — the proof, not just the claim
- [ ] `substreams run … graph_out` producing entities on Unichain
- [ ] Studio subgraph answering the same question
- [ ] Hosted `rank_pools` / `suggest_move` output, including a refusal
- [ ] Local `propose_move` → simulate → `execute_move`
- [ ] Explorer page for the transaction
- [ ] Gas comparison on screen as two numbers, not a claim in the voice-over

## Preconditions before recording

1. A manager created from the 2.1.0 implementation, with at least two pools configured.
2. Its oracle wired (`setPriceOracle`) and the operator authorised.
3. Enough USDC on it to make the numbers legible on screen.
4. The subgraph deployed in Studio and synced past the manager's creation block.
5. Both sinks running, so "live data" is true at the moment of recording.
