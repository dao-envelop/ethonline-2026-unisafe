# Generates the ETHOnline submission logo + cover as SVG, with text widths measured from the
# actual brand fonts so nothing has to be eyeballed or nudged after the fact.
import re, json, pathlib

FONTS = {
    "sgb": "/home/devops/.fonts/SGBold.ttf",
    "sgm": "/home/devops/.fonts/SGMedium.ttf",
    "hgr": "/home/devops/.fonts/HGRegular.ttf",
    "hgs": "/home/devops/.fonts/HGSemiBold.ttf",
    "jbm": "/home/devops/.fonts/JBMMedium.ttf",
}
FAMILY = {"sgb": "SG Bold", "sgm": "SG Medium", "hgr": "HG Regular", "hgs": "HG SemiBold", "jbm": "JBM Medium"}

from fontTools.ttLib import TTFont
_cache = {}
def _metrics(key):
    if key not in _cache:
        f = TTFont(FONTS[key])
        cmap = f.getBestCmap()
        hmtx = f["hmtx"].metrics
        _cache[key] = (cmap, hmtx, f["head"].unitsPerEm)
    return _cache[key]

def w(text, key, size):
    cmap, hmtx, upem = _metrics(key)
    total = 0
    for ch in text:
        g = cmap.get(ord(ch))
        total += hmtx[g][0] if g and g in hmtx else upem // 2
    return total * size / upem

BG, S1, TX, TX2, TX3 = "#0A0C10", "#101319", "#EAEEF4", "#9AA4B2", "#626C7A"
MINT, MINT2, ACC = "#4AFEBF", "#51EEDA", "#34E3AC"

# The Envelop mark, lifted verbatim from stablelp-ui/src/app/icon.svg (viewBox 0 0 120 120) so the
# submission artwork and the app's own favicon are the same drawing, not a redraw.
ICON = pathlib.Path("/home/devops/codex-work/ev2/stablelp-ui/src/app/icon.svg").read_text()
inner = ICON.split(">", 1)[1].rsplit("</svg>", 1)[0].strip()

def mark(x, y, px, suffix):
    """The mark placed at (x, y) at px × px. Gradient ids are suffixed so two copies can coexist."""
    body = re.sub(r'(paint\d_linear_1718_3882)', r'\1_' + suffix, inner)
    return f'<g transform="translate({x},{y}) scale({px/120:.6f})">{body}</g>'

def text(s, x, y, key, size, fill, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{FAMILY[key]}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{s}</text>')

# ---------------------------------------------------------------- logo, 512 × 512
L = 512
logo = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{L}" height="{L}" viewBox="0 0 {L} {L}">']
logo.append(f'''<defs>
<radialGradient id="glow" cx="0.5" cy="0.32" r="0.72">
  <stop offset="0" stop-color="{MINT}" stop-opacity="0.22"/>
  <stop offset="1" stop-color="{MINT}" stop-opacity="0"/>
</radialGradient>
</defs>''')
logo.append(f'<rect width="{L}" height="{L}" rx="112" fill="{BG}"/>')
logo.append(f'<rect width="{L}" height="{L}" rx="112" fill="url(#glow)"/>')
logo.append(f'<rect x="1.5" y="1.5" width="{L-3}" height="{L-3}" rx="110.5" fill="none" '
            f'stroke="{ACC}" stroke-opacity="0.28" stroke-width="3"/>')
MK = 300
logo.append(mark((L - MK) / 2, (L - MK) / 2 - 6, MK, "a"))
logo.append("</svg>")
pathlib.Path(f"{pathlib.Path(__file__).parent}/logo-512.svg").write_text("\n".join(logo))

# ---------------------------------------------------------------- cover, 1280 × 720 (16:9)
W, H, M = 1280, 720, 72
c = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
c.append(f'''<defs>
<radialGradient id="g1" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="{MINT}" stop-opacity="0.16"/><stop offset="1" stop-color="{MINT}" stop-opacity="0"/>
</radialGradient>
<radialGradient id="g2" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="{MINT2}" stop-opacity="0.07"/><stop offset="1" stop-color="{MINT2}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="arrow" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{MINT2}"/><stop offset="1" stop-color="{MINT}"/>
</linearGradient>
<marker id="head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,1 L9,5 L0,9 z" fill="{MINT}"/>
</marker>
</defs>''')
c.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
c.append(f'<ellipse cx="1010" cy="150" rx="620" ry="480" fill="url(#g1)"/>')
c.append(f'<ellipse cx="90" cy="700" rx="520" ry="380" fill="url(#g2)"/>')

# header
c.append(mark(M, 66, 54, "b"))
c.append(text("unisafe", M + 54 + 18, 110, "sgb", 40, TX))
c.append(text("ETHOnline 2026", W - M, 104, "jbm", 20, TX3, anchor="end"))
c.append(f'<rect x="{M}" y="150" width="{W-2*M}" height="1" fill="#FFFFFF" fill-opacity="0.08"/>')

# headline
HS, LH = 52, 64
for i, line in enumerate(["Move liquidity between", "Uniswap v4 pools", "in one transaction."]):
    c.append(text(line, M, 252 + i * LH, "sgb", HS, TX))
c.append(text("And let an agent decide when to.", M, 252 + 3 * LH + 18, "hgr", 25, TX2))

# the move, drawn: two pools, one unlock boundary, one guarded swap path between them
BX, BY, BW, BH = 776, 206, 432, 268
c.append(f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="26" fill="{MINT}" fill-opacity="0.03" '
         f'stroke="{ACC}" stroke-opacity="0.32" stroke-width="2" stroke-dasharray="7 7"/>')
lbl, lsz = "one  unlock", 16
lw = w(lbl, "jbm", lsz)
c.append(f'<rect x="{BX+28}" y="{BY-12}" width="{lw+24}" height="24" rx="12" fill="{BG}"/>')
c.append(text(lbl, BX + 28 + 12, BY + 5, "jbm", lsz, ACC))

CY = BY + 118
for cx, name, fee in ((BX + 96, "Pool A", "0.05%"), (BX + BW - 96, "Pool B", "0.30%")):
    c.append(f'<circle cx="{cx}" cy="{CY}" r="54" fill="{MINT}" fill-opacity="0.09" stroke="{ACC}" '
             f'stroke-opacity="0.45" stroke-width="2"/>')
    c.append(text(fee, cx, CY + 7, "jbm", 19, TX, anchor="middle"))
    c.append(text(name, cx, CY + 86, "hgs", 19, TX2, anchor="middle"))

x0, x1 = BX + 96 + 62, BX + BW - 96 - 62
c.append(f'<path d="M{x0},{CY-22} C{x0+40},{CY-74} {x1-40},{CY-74} {x1},{CY-22}" fill="none" '
         f'stroke="url(#arrow)" stroke-width="3.5" stroke-linecap="round" marker-end="url(#head)"/>')
c.append(text("moveLiquidity()", (x0 + x1) / 2, CY - 72, "jbm", 19, MINT, anchor="middle"))

# track chips — the three tracks this is submitted under
cx0, CHS = M, 18
for chip in ("Uniswap v4", "Chainlink", "The Graph"):
    cw = w(chip, "jbm", CHS) + 30
    c.append(f'<rect x="{cx0}" y="498" width="{cw:.1f}" height="38" rx="19" fill="{MINT}" fill-opacity="0.06" '
             f'stroke="{ACC}" stroke-opacity="0.28" stroke-width="1.5"/>')
    c.append(text(chip, cx0 + 15, 523, "jbm", CHS, TX2))
    cx0 += cw + 14

# footer facts
c.append(f'<rect x="{M}" y="600" width="{W-2*M}" height="1" fill="#FFFFFF" fill-opacity="0.08"/>')
facts = "337,035 gas   ·   one settlement pass   ·   one oracle check"
c.append(text(facts, M, 648, "jbm", 19, TX2))
c.append(text("unisafe.envelop.is", W - M, 648, "jbm", 19, ACC, anchor="end"))
c.append("</svg>")
pathlib.Path(f"{pathlib.Path(__file__).parent}/cover-1280x720.svg").write_text("\n".join(c))

print(json.dumps({
    "headline_widths": [round(w(t, "sgb", HS)) for t in ["Move liquidity between", "Uniswap v4 pools", "in one transaction."]],
    "column_budget": BX - M - 40,
    "sub": round(w("And let an agent decide when to.", "hgr", 25)),
    "facts": round(w(facts, "jbm", 19)),
 "chips_end": round(cx0 - 14),
    "facts_budget": W - 2 * M - round(w("unisafe.envelop.is", "jbm", 19)) - 40,
}, indent=1))
