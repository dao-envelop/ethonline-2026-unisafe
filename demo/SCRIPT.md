# Demo video — script and shot list

Target length **2:50–3:20**. The through-line is an **agent operating real money under a contract-enforced
boundary**: a person sets the manager up in the dApp, hands an agent the operator role, the agent does the
work in conversation, and the dApp confirms what happened. No CLI, no curl — those prove the plumbing, not
the product.

Chain: **Unichain** (both implementations allowlisted in the factory, oracle seeded with feeds, the index
follows that chain live). Manager created fresh from the 2.1.0 implementation, so `moveLiquidity` exists on
it.

---

## Act 1 · 0:00 – 0:50 · A person sets it up, by hand

**On screen:** unisafe.envelop.is. Create a manager with two pools, deposit, done. Real wallet, real
signatures, at speed — this act is deliberately unglamorous.

> A manager is an NFT that owns Uniswap v4 liquidity. Whoever holds the NFT owns the funds. I create one,
> pick two pools, and deposit.

**Then the beat the whole video rests on** — the Operators tab, adding the agent's address:

> Now I give an agent the operator role. An operator can rebalance this manager and can never withdraw
> from it. That is not a policy in the agent's prompt, it is the contract: there is no code path from an
> operator to my principal. Every swap and every liquidity add it makes is also checked against a
> Chainlink price — the manager rejects its own operator if the price is wrong.

Show the card that says the oracle is wired, and the warning next to the operator field: granting an
operator is bounded, approving the NFT is not.

---

## Act 2 · 0:50 – 2:20 · The agent takes over

**On screen:** an agent session with two MCP servers connected. Nothing typed but plain sentences.

**Beat 1 — it can see (0:50–1:20).** *"What does this manager hold, and what has it done?"*

The answer comes back with positions, fees and a timeline — and says where it came from: our Substreams
index, current to a block number.

> The reading half runs on our server. It has no key and cannot sign anything. It answers from an index
> we build from the chain with Substreams — the same package published on substreams.dev, filtered
> through another published package's block index so it only opens blocks that concern us.

**Beat 2 — it puts the money to work (1:20–1:45).** *"Deploy the idle balance."*

Show the proposal: pools, ticks, amounts, and the policy verdict. Then approve, and the transaction lands.

> The agent proposes; the local half checks it against a policy, simulates it, and only then signs. The
> half that holds the key makes no outbound call except to the chain.

**Beat 3 — it decides where to be (1:45–2:20).** *"Is this the best pool for it?"*

The agent ranks the manager's own pools by fee APR and answers with a number, not an opinion — including
the pools it could not score, and why.

> It only considers pools the owner fixed into the manager at creation. It cannot invent a destination,
> because the contract would reject one.

Then: *"Move it."*

> One transaction. Liquidity comes out of one pool, is swapped if it needs to be, and goes into another
> inside a single Uniswap v4 unlock. Two transactions became one — about 66,000 gas less, and gone with
> them is the window where the capital sat idle between closing and opening.

**Show on screen while it executes:** the hosted service returned *numbers* — a pool id, two ticks, an
amount — and the local server re-derived them against chain state before signing. Nothing that could be
signed ever crossed the network.

---

## Act 3 · 2:20 – 2:50 · Back to the dApp, which agrees

**On screen:** refresh the manager page. The position is in the new pool, with the new range. Open the
history: it says **"From our index, current to block N"**.

> Same manager, same NFT, same owner. The agent moved the position and could never have taken it. And
> the app is reading the same index the agent reasoned over — the caption says which source answered and
> how current it is, because "from our index" and "read from your browser" are not the same promise.

---

## Act 4 · 2:50 – 3:10 · What this does not do

Short, plain, and the reason the rest is credible.

> Managers are non-upgradeable clones, so the cross-pool move reaches managers created from this
> deployment onward — not the ones already live. The index follows Ethereum and Unichain; Arbitrum stays
> on our own indexer, because per-block billing and quarter-second blocks are bad arithmetic. And the
> ranking is fee APR over a completed day — it is not a forecast, and impermanent loss is not in it.

---

## Close · 3:10 – 3:20

Repositories, file-and-line pointers per track, `FEEDBACK.md`.

---

## Shot checklist

- [ ] Manager creation in the dApp — two pools, deposit, wallet signatures
- [ ] Operators tab: adding the agent's address, oracle card visible
- [ ] Agent answers a portfolio question with the index provenance visible
- [ ] Agent proposes an allocate; the policy verdict and simulation on screen
- [ ] Agent ranks pools, including a refusal with its reason
- [ ] `propose_move` → `execute_move`, transaction hash, explorer
- [ ] Gas comparison on screen as two numbers, not a claim in the voice-over
- [ ] dApp after the move: new pool, new range, "From our index, current to block N"
- [ ] Two seconds on `test/CrossPoolUnlock.t.sol` — the proof that several pools in one unlock is legal

## Preconditions

1. ~~Manager created from the 2.1.0 implementation with at least two pools~~ — done (`0x7C77e35F…`).
2. ~~Oracle wired and seeded~~ — done on Unichain.
3. ~~Index following that chain~~ — done; `suggest_move` already answers on this manager (1.30% → 9.27%).
4. **Operator wallet authorised on the manager** — the one the local MCP server holds. Not done.
5. **Enough USDC on it that the numbers read on screen.** Not done.
6. A second manager, created live in Act 1, so the video shows the setup rather than referring to it.
   The one from precondition 1 stays as the rehearsal.

## Things to avoid on camera

- Any terminal that is not the agent session. curl proves plumbing; it undercuts the point.
- Reading numbers the agent already said aloud.
- Claiming "AI decides" where the contract decides. The interesting part is the opposite: what the agent
  is *not* allowed to do, and who enforces it.

## End cards

Two slides to cut in after the last shot, in [`slides/`](slides/): the concept in one picture, then
what existed versus what was built during the event with the sponsor technology tagged on each line.
1920 × 1080, hold each 6–8 seconds. They close the video on the claim the demo just showed rather than
on a screen recording fading out.
