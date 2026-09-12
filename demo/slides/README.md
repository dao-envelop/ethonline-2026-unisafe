# End cards

Two 1920 × 1080 slides to cut in after the demo, in this order.

| File | Says |
|---|---|
| `slide-1-concept.png` | the whole solution in one picture: The Graph → agent → vault → Uniswap v4 pools, with the Chainlink gate on the operator call and the owner's NFT as the only path to withdraw |
| `slide-2-scope.png` | two columns — what existed before 4 September, and what was built during the event, each line tagged with the sponsor technology it uses |

Full HD, so they drop into a 1080p timeline at 100% with no scaling. Hold each for **6–8 seconds** —
slide 2 is five lines of reading. Both are dark (`#0A0C10`), matching the dApp, so a cut from screen
recording to slide does not flash.

`slides.py` regenerates both from the same mark and measured type as the rest of the artwork — see
[`../../brand/README.md`](../../brand/README.md) for the font setup. Text wraps on measured width, so
editing a line cannot silently overflow a column; the script prints where the right column ends
(keep it under 960).

The [pitch deck](https://dao-envelop.github.io/ethonline-2026-unisafe/) embeds these two
SVGs as its closing slides (`docs/assets/`), so edit them here and copy across — the deck must
not drift from what a viewer just watched.
