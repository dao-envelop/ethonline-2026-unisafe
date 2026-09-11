# Submission artwork

| File | Size | Where it goes |
|---|---|---|
| `logo-512.png` | 512 × 512 | ETHGlobal **Logo** — square icon |
| `cover-1280x720.png` | 1280 × 720 | ETHGlobal **Cover image** (16:9) — upload this one |
| `cover-640x360.png` | 640 × 360 | the same cover at the minimum stated size, if the form rejects the large one |

The mark is the app's own favicon (`stablelp-ui/src/app/icon.svg`), lifted verbatim rather than
redrawn, so the submission card and the product show the same drawing. Colours are the app's tokens —
ground `#0A0C10`, accent `#34E3AC`, mint gradient `#4AFEBF` → `#51EEDA`. Type is the app's own
Space Grotesk / Hanken Grotesk / JetBrains Mono.

Every number on the cover is one we measured: **337,035 gas** is `moveLiquidity` from equal fresh
state (`test/VolatileLPManagerMove.t.sol`), against 381,744 + 21,000 for the two-call path.

## Regenerating

`make-assets.py` writes both SVGs, measuring every string against the real font files so the layout
never needs nudging by hand. It needs `fonttools` and the three brand fonts installed as static
instances — the variable `.woff2` files in `stablelp-ui/src/app/fonts/` instanced at the weights the
script names (`SG Bold`, `SG Medium`, `HG Regular`, `HG SemiBold`, `JBM Medium`) and dropped into
`~/.fonts`. Rasterise with sharp at 4× density, then downscale:

```js
sharp("cover-1280x720.svg", { density: 192 }).resize(1280, 720).png().toFile("cover-1280x720.png")
```
