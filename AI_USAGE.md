# AI usage disclosure

ETHOnline asks entrants to document where AI was used, to use it as assistance rather than to generate a
project wholesale, and to keep human contribution meaningful. This file is that disclosure. It is written
plainly rather than defensively — the tooling is visible in our commit history anyway, and we would rather
state it than have a judge infer it.

## What is used

**Claude Code** (Anthropic), as a pair-programming and research tool, across all five workstreams. Commits
it co-authored carry a `Co-Authored-By: Claude` trailer, so the extent is auditable from `git log` rather
than from this file's word.

It is used for: reading unfamiliar code and reporting what is actually there, drafting implementations and
tests, running builds and test suites, checking facts against live sources (contract state, RPC, published
documentation), and writing prose such as this file.

## What it is not used for

Architecture and product decisions are made by the human owner of the project. Every non-trivial choice in
[PLAN.md](PLAN.md) — splitting the agent server into a key-holding local half and a hosted read half, making
the index the primary read path with the existing oracle as fallback, leaving the stablecoin manager
untouched, doing the breaking package split inside the event rather than after it, choosing which chains to
index against a block quota, and where to host — was made by a person, in several cases against the first
recommendation the model gave.

The model does not decide what ships. Code it writes is reviewed, and it is regularly wrong in ways that
matter: during planning for this project it asserted our repositories were private when they are public,
and it proposed a design based on a branch it had not checked, which turned out to contain no code. On 8
September it started a verification run against Arbitrum — a chain the owner had explicitly excluded from
indexing because of the block quota — and was stopped by the owner before the run cost anything. The same
day it was wrong in the opposite direction too, believing a start block would keep a backfill cheap; the
stores backfill from the manifest's `initialBlock` regardless, which is why Unichain is indexed from a
recent block rather than from the factory. All four were caught by verification or by a person, and all
four are recorded in the plan's log rather than tidied away.

## Prior work

This project extends a codebase built over the preceding months, itself written with the same tooling under
the same conditions. What predates the event is listed in the
[README](README.md#what-existed-before-the-hackathon); only work done between 4 and 13 September 2026 is
offered for judging.

## Third-party AI-authored content

None. No generated assets, art, or copied third-party AI output are included. External code comes from
named open-source dependencies with their own licences: Uniswap v4 core and periphery, OpenZeppelin,
Foundry, Substreams SDKs, viem, and Next.js.
