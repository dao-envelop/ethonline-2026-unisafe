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
