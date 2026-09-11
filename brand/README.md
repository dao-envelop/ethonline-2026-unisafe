# Submission artwork

| File | Size | Where it goes |
|---|---|---|
| `logo-512.png` | 512 × 512 | ETHGlobal **Logo** — square icon |
| `cover-1280x720.png` | 1280 × 720 | ETHGlobal **Cover image** (16:9) — upload this one |
| `cover-640x360.png` | 640 × 360 | the same cover at the minimum stated size, if the form rejects the large one |
| `logo-64.png`, `logo-small.svg` | 64 × 64 | small-size build: the floating arc is drawn unbroken, because below ~40 px its 20 px gap collapses into a smudge |

## The mark

Not Envelop's mark, and not a rebrand either — Envelop's mark with a subtraction. The outer broken
ring, its 94° right arc and the floating crumb at 158° are kept **verbatim**, so the family reads at a
glance. The rhombus loses its two upper edges, and what is left is a **V**: a vessel with no outlet,
holding the core bead, with a shallow broken arc floating above it.

That is the product's one claim, drawn: **the moving part is curved, broken and above the line; the
held part is angular, closed and below it.** An operator may rebalance across pools; nothing reaches
the principal. The V is also the *v* of v4 — the only nod to Uniswap in the mark, and a letterform we
already owned, since the rhombus contained it all along. No Uniswap asset, no unicorn, no `#FF007A`,
no padlock.

The runner-up — the rhombus filled solid below the waist with a void where the core was — was drawn
and rejected: at every size it reads as an eye or a camera aperture.

Colours are the app's tokens: ground `#0A0C10`, accent `#34E3AC`, mint gradient `#4AFEBF` → `#51EEDA`.
Type on the cover is the app's own Space Grotesk / Hanken Grotesk / JetBrains Mono.

Every number on the cover is one we measured: **337,035 gas** is `moveLiquidity` from equal fresh
state (`test/VolatileLPManagerMove.t.sol`), against 381,744 + 21,000 for the two-call path.

Note that `stablelp-ui/src/app/icon.svg` — the app's own favicon — is **still the Envelop mark**.
Adopting this one in the product is a separate decision; `mark.py` carries the geometry on a 512 grid
and scales to the 120 grid the favicon uses.

## Regenerating

`mark.py` holds the mark, `make-assets.py` writes both SVGs — measuring every string against the real
font files, so the layout never needs nudging by hand. It needs `fonttools` and the three brand fonts
installed as static instances: the variable `.woff2` files in `stablelp-ui/src/app/fonts/` instanced at
the weights the script names (`SG Bold`, `SG Medium`, `HG Regular`, `HG SemiBold`, `JBM Medium`) and
dropped into `~/.fonts`. Rasterise with sharp at 4× density, then downscale:

```js
sharp("cover-1280x720.svg", { density: 192 }).resize(1280, 720).png().toFile("cover-1280x720.png")
```
