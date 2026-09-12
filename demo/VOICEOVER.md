# Video voice-over — running script

English narration for the demo body, segment by segment, each counted against its hold. Confident
narration is **145–160 words per minute**, so the budget is **~2.5 words per second**:

| Hold | Words |
|---|---|
| 5 s | 12–14 |
| 7 s | 17–19 |
| 10 s | 25–27 |

A line written by ear always runs long, and the cost is paid on camera — the read gets rushed and the
last three words land after the cut. Everything below is counted.

Say **"uni-safe"**, and read `moveLiquidity` / `suggest_move` as ordinary words.

---

## 1 · 5 s — what this is

**Recommended — 14 words**

> Meet unisafe: a personal smart wallet that runs your Uniswap v4 positions — agents included.

**If "true web3 dapp" must stay — 17 words, needs 6.5 s**

> unisafe is a true web3 dapp: a personal smart wallet running your Uniswap v4 positions, agents included.

At five seconds you can have *"true web3 dapp"* or *"agents"*, not both. Keep agents: it is the only
half a viewer cannot guess from the screen, and it is what the whole video is about. "True web3 dapp"
is a claim the demo proves by itself — the wallet is an NFT, the keys are the viewer's — so spending a
fifth of the segment asserting it buys nothing.

## 2 · 5 s — how it works

**Recommended — 13 words**

> How it works: create a manager, deposit your coins, and it opens a position.

**Tighter, if the shot is busy — 12 words**

> Create a manager, deposit your coins, and the manager opens a position.

Keep "manager" as the word — it is what the UI calls it, and the viewer is looking at it.

## 3 · 22 s — creating a manager, and why the pool list is the product

**Recommended — 49 words**

> I already have managers running, but let's create one. ⏸
> The step that matters is choosing the pools. ⏸
> A manager can only ever hold positions in the pools you pick here — that is the security model. ⏸
> No operator and no agent can reach anything else. ⏸
> Up to thirty-two, chosen once.

49 words is 20 seconds of speech, and the four ⏸ beats spend the rest. Do not fill them: the pauses are
where the claim lands, and this is the one segment in the video that explains *why* an agent is safe to
authorise at all.

**"Chosen once" is literally true** — `_registerPool` is internal and reachable only from `initialize`;
there is no function that adds a pool to a live manager, and the managers are non-upgradeable clones.
Say it plainly.

**If you come in fast and need one more line:**

> It is the boundary, drawn before anyone is let in.

Say "thirty-two", not "thirty two" — and let the number sit at the end, where the UI shows the count.

## 4 · 9 s — the manager is an NFT

**22 words**

> Every manager is an NFT — hold the token, own the funds. ⏸
> Its metadata is drawn on chain, updating as the positions do.

"Drawn on chain" is exact: `tokenURI` renders through `WalletPositionDescriptor`, which walks the open
salts and values each position itself; every mutation emits ERC-4906 `MetadataUpdate`. No server draws
this. Worth saying precisely — half the audience has only seen NFTs whose art is a URL.

## 5 · 7 s — the operator

**18 words**

> Here is the key part: you can authorise an operator to manage the positions — and only manage them.

The last four words are the segment. Do not drop them to save time; without them this is just a
permissions screen, and with them it is the reason the rest of the video exists.

## 6 · 7 s — authorising it

**17 words**

> I already have an EVM account for this. Paste the address, sign the transaction, and it's authorised.

Say "E-V-M", three letters.

---

**Note on the arithmetic:** these three were given as 35 seconds, but 9 + 7 + 7 is 23. Either there are
~12 seconds of silent screen between them, or a fourth beat is missing. Say which and the gap gets a
line — or leave it silent, which is a fine choice right after the operator claim lands.

## 7 · 12 s — the address is set, and the guard behind it

**28 words**

> There it is — authorised. ⏸
> And the operator cannot move your money at a bad price: every action is checked against a Chainlink
> feed. ⏸ Out of bounds, it reverts.

**A precision worth keeping.** The guard is a *price* bound, not a judge of good and bad trades — it
compares the swap price, the pool's own price and where a range would sit against the feed, and refuses
outside the tolerance. Say "at a bad price", not "economically wrong": the narrower claim is the one
that is true, and it is the more impressive one, because it is enforced rather than promised.

**If you have room, the strongest single line here:**

> With no feed configured, the operator cannot act at all.

That is fail-closed, and it is unusual enough to be worth the breath.

---

# 1:06 → 2:43

## 8 · 1:06–1:13 (7 s) — the agents page · 18 words

> Connecting an agent has its own page — slash agents. Claude, Codex, whatever you run: the instructions
> are there.

Read the URL as "slash agents"; spelling out the domain costs three seconds and the screen shows it.

## 9 · 1:13–1:22 (9 s) — starting the agent · 23 words

> I'll start my agent in a folder of its own, with nothing set up, and simply ask what it can do with this.

"Nothing set up" is worth the words — an empty folder is the proof that the skill and the server carry
the knowledge, not a prepared workspace.

## 10 · 1:22–1:29 (7 s) — it connects · 18 words

> First it connects to our hosted MCP server — no key, read only — and lists what it can do.

## 11 · 1:29–1:43 (14 s) — why that server exists · 34 words

> That server exists for one job: letting an agent read your manager — the positions it holds, the fees
> they've earned. ⏸ It holds no key, so the worst it can do is tell you something.

The last clause is the one to land. A read-only server is not a limitation to apologise for; it is the
reason it can be hosted at all.

## 12 · 1:44–1:50 (6 s) — the address · 15 words

> Just copy the manager's address out of the browser and hand it to your agent.

## 13 · 1:50–1:58 (8 s) — the answer · 19 words

> Give it a moment, and you get the whole picture — every position, what it's worth, what it has earned.

## 14 · 1:58–2:06 (8 s) — another chain · 19 words

> Let's try another manager, on a different chain. Same question, same tools — the agent doesn't need to
> know which.

## 15 · 2:06–2:18 (12 s) — the local server · 29 words

> To let the agent actually send transactions, you install the local MCP server — the one that holds the
> operator account we authorised earlier. ⏸ That key never leaves your machine.

## 16 · 2:18–2:43 (25 s) — the move · 56 words

> Now we can ask for something real: move liquidity from one pool into another, with a swap in the middle,
> in a single transaction. ⏸
> The agent works out the route, the local server signs it, and the contract checks the price before
> anything moves. ⏸
> Back in the browser: closed in one pool, open in the other.

56 words is 22 seconds; the two beats spend the rest. This is the payoff of the whole video — three
parties each doing exactly one job, named in order. Do not add a fourth clause.
