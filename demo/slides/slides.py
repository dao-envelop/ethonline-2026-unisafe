# Two end-card slides for the demo video, 1920 × 1080. Same mark, palette and type as the rest of the
# submission. Text is measured against the real fonts and wrapped on measured width, so nothing has to
# be nudged by eye and a copy edit cannot silently overflow a column.
import pathlib
from mark import mark, BG, ACC, MINT, MINT2
from gen import w, text, FAMILY, TX, TX2, TX3, S1

W, H = 1920, 1080

def wrap(s, key, size, width):
    words, lines, cur = s.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if w(trial, key, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines

def head(o, eyebrow, title, sub=None):
    o.append(mark(100, 74, 56, "h", simplified=True))
    o.append(text("unisafe", 100 + 56 + 16, 118, "sgb", 38, TX))
    o.append(text(eyebrow, W - 100, 114, "jbm", 22, TX3, anchor="end"))
    o.append(f'<rect x="100" y="156" width="{W-200}" height="1" fill="#FFFFFF" fill-opacity="0.09"/>')
    o.append(text(title, 100, 268, "sgb", 58, TX))
    if sub:
        o.append(text(sub, 100, 320, "hgr", 27, TX2))

def frame(inner):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
<radialGradient id="s1" cx="0.5" cy="0.5" r="0.5">
<stop offset="0" stop-color="{MINT}" stop-opacity="0.13"/><stop offset="1" stop-color="{MINT}" stop-opacity="0"/></radialGradient>
<radialGradient id="s2" cx="0.5" cy="0.5" r="0.5">
<stop offset="0" stop-color="{MINT2}" stop-opacity="0.06"/><stop offset="1" stop-color="{MINT2}" stop-opacity="0"/></radialGradient>
<marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M0,1.2 L9,5 L0,8.8 z" fill="{ACC}"/></marker>
</defs>
<rect width="{W}" height="{H}" fill="{BG}"/>
<ellipse cx="1520" cy="180" rx="820" ry="620" fill="url(#s1)"/>
<ellipse cx="180" cy="1020" rx="700" ry="520" fill="url(#s2)"/>
{inner}</svg>'''

# ============================================================ slide 1 — the concept
o = []
head(o, "THE CONCEPT", "An agent may move the money. It can never take it.",
     "One vault, any Uniswap v4 pool, and a boundary the contract enforces instead of trusting anyone.")

BOXES = [
    (100,  300, "The Graph", "index of every position,\nfee and move"),
    (520,  300, "Agent", "reads, ranks,\nproposes"),
    (940,  400, "Manager NFT vault", "holds the capital,\nowns the positions"),
    (1460, 360, "Uniswap v4", "the pools the\nliquidity sits in"),
]
BY, BH = 520, 168
for x, bw, title, body in BOXES:
    strong = title.startswith("Manager")
    o.append(f'<rect x="{x}" y="{BY}" width="{bw}" height="{BH}" rx="20" fill="{S1}" '
             f'stroke="{ACC}" stroke-opacity="{0.55 if strong else 0.22}" stroke-width="{2.5 if strong else 1.5}"/>')
    o.append(text(title, x + bw / 2, BY + 62, "sgb", 31, MINT if strong else TX, anchor="middle"))
    for i, ln in enumerate(body.split("\n")):
        o.append(text(ln, x + bw / 2, BY + 104 + i * 29, "hgr", 21, TX2, anchor="middle"))

ARROWS = [(400, 520, "ranked facts"), (820, 940, "operator call"), (1340, 1460, "one unlock")]
for x0, x1, label in ARROWS:
    o.append(f'<path d="M{x0+12} {BY+BH/2} L{x1-14} {BY+BH/2}" stroke="{ACC}" stroke-width="3" '
             f'stroke-linecap="round" marker-end="url(#ah)"/>')
    o.append(text(label, (x0 + x1) / 2, BY - 18, "jbm", 18, TX3, anchor="middle"))

# the owner's key, above the vault
o.append(f'<path d="M1140 {BY-70} L1140 {BY-12}" stroke="{ACC}" stroke-opacity="0.5" stroke-width="2.5" '
         f'stroke-dasharray="6 6" stroke-linecap="round"/>')
o.append(text("Owner holds the NFT — the only path to withdraw", 1140, BY - 86, "hgs", 23, TX, anchor="middle"))

# the Chainlink gate, on the operator arrow
GX = 880
o.append(f'<path d="M{GX} {BY+BH/2+14} L{GX} {BY+BH+96}" stroke="{ACC}" stroke-opacity="0.5" '
         f'stroke-width="2.5" stroke-dasharray="6 6" stroke-linecap="round"/>')
o.append(f'<circle cx="{GX}" cy="{BY+BH/2}" r="13" fill="{BG}" stroke="{ACC}" stroke-width="3"/>')
gl = "Chainlink checks every operator action — the swap price, the pool's own price, and where a range may sit"
for i, ln in enumerate(wrap(gl, "hgr", 23, 760)):
    o.append(text(ln, GX, BY + BH + 130 + i * 31, "hgr", 23, TX2, anchor="middle"))

o.append(f'<rect x="100" y="928" width="{W-200}" height="1" fill="#FFFFFF" fill-opacity="0.09"/>')
o.append(text("The agent proposes. The contract decides. The owner keeps the key.", 100, 984, "sgb", 30, MINT))
o.append(text("unisafe.envelop.is", W - 100, 984, "jbm", 22, TX3, anchor="end"))
pathlib.Path(f"{pathlib.Path(__file__).parent}/slide-1-concept.svg").write_text(frame("\n".join(o)))

# ============================================================ slide 2 — before / during
o = []
head(o, "SCOPE", "What existed, and what we built in nine days.",
     "The left column is prior work and is not what we are asking to be judged.")

LX, RX, TOP = 100, 1020, 372
LW, TAGW, RW = 780, 132, 660
o.append(text("BEFORE  ·  4 September", LX, TOP, "jbm", 22, TX3))
o.append(text("BUILT DURING THE EVENT", RX, TOP, "jbm", 22, MINT))
o.append(f'<rect x="{LX}" y="{TOP+18}" width="{LW}" height="1" fill="#FFFFFF" fill-opacity="0.09"/>')
o.append(f'<rect x="{RX}" y="{TOP+18}" width="{TAGW+RW}" height="2" fill="{ACC}" fill-opacity="0.5"/>')

BEFORE = [
    "NFT-owned managers over Uniswap v4 — live and non-upgradeable on five chains, ~24k audited lines",
    "The operator model: rebalance yes, withdraw never — enforced by the contract, not by trust",
    "recenter — remove, swap and re-add inside one pool",
    "The dApp, and a local MCP server giving an agent the operator role, running since July",
    "An event indexer over five chains, serving position history to the frontend",
]
# The sponsor tag is a label column, not a row of its own: a slide has to be read in four seconds.
DURING = [
    ("Uniswap", "moveLiquidity — a cross-pool move in one unlock. 337,035 gas, one settlement pass, "
                "no idle window."),
    ("Chainlink", "The operator guard extended from swap prices to every action, plus a bound on where "
                  "a range may sit. New oracle deployed and seeded on five chains."),
    ("The Graph", "A Substreams package, published and composed with a third-party block index, feeding "
                  "a SQL index on Ethereum and Unichain."),
    ("The Graph", "A hosted read/strategy MCP server: history, pool ranking, suggest_move — every answer "
                  "naming its source and how far behind it is."),
    (None, "In the dApp: move between pools, operators read from the contract, the oracle card, and an "
           "entry point built for agents."),
]

SZ, LH = 22, 29
y = TOP + 66
for item in BEFORE:
    lines = wrap(item, "hgr", SZ, LW - 34)
    o.append(f'<circle cx="{LX+6}" cy="{y-7}" r="4" fill="{TX3}"/>')
    for i, ln in enumerate(lines):
        o.append(text(ln, LX + 26, y + i * LH, "hgr", SZ, TX2))
    y += len(lines) * LH + 24

y = TOP + 66
for tag, item in DURING:
    lines = wrap(item, "hgr", SZ, RW)
    if tag:
        tw = w(tag, "jbm", 16) + 22
        o.append(f'<rect x="{RX}" y="{y-21}" width="{tw:.1f}" height="27" rx="13.5" fill="{MINT}" '
                 f'fill-opacity="0.10" stroke="{ACC}" stroke-opacity="0.38" stroke-width="1.2"/>')
        o.append(text(tag, RX + 11, y - 2, "jbm", 16, MINT))
    else:
        o.append(f'<circle cx="{RX+10}" cy="{y-8}" r="4" fill="{ACC}"/>')
    for i, ln in enumerate(lines):
        o.append(text(ln, RX + TAGW, y + i * LH, "hgr", SZ, TX))
    y += len(lines) * LH + 24

o.append(f'<rect x="100" y="960" width="{W-200}" height="1" fill="#FFFFFF" fill-opacity="0.09"/>')
o.append(text("Submitted under Continuity — Extend Open Source", 100, 1012, "hgs", 25, TX2))
o.append(text("github.com/dao-envelop/ethonline-2026-unisafe", W - 100, 1012, "jbm", 20, TX3, anchor="end"))
pathlib.Path(f"{pathlib.Path(__file__).parent}/slide-2-scope.svg").write_text(frame("\n".join(o)))
print("right column ends at", y)
