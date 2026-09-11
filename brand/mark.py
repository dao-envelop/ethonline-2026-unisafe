# The unisafe mark, concept "Vee": Envelop's rhombus with its two upper edges subtracted, so what
# is left is a sealed vessel holding the core bead, with a broken arc floating above it. Every
# number here is the designer's; the 512-grid is authoritative and everything else scales from it.
BG, ACC, MINT, MINT2 = "#0A0C10", "#34E3AC", "#4AFEBF", "#51EEDA"

RING = [
    'M 256 67.4 A 188.6 188.6 0 0 0 256 444.6',      # left half, 12 → 6 through the left
    'M 384.6 118.1 A 188.6 188.6 0 0 1 384.6 393.9',  # right quarter, 43° → 137°
]
CRUMB = (326.4, 430.2, 15.5)                          # the floating end of the ring, at 158°

def defs(sfx):
    return (f'<linearGradient id="mg{sfx}" x1="0" y1="54" x2="0" y2="458" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{MINT}"/><stop offset="1" stop-color="{MINT2}"/></linearGradient>')

def body(sfx, simplified=False):
    """The mark itself on a 512 grid, centred at (256, 256). `simplified` closes the arc's break —
    below ~40 px the 20 px gap collapses to a smudge, so it is drawn as one piece instead."""
    g = f'url(#mg{sfx})'
    o = [f'<g fill="none" stroke="{g}" stroke-width="28.8" stroke-linecap="round">']
    o += [f'<path d="{d}"/>' for d in RING]
    o.append('</g>')
    o.append(f'<circle cx="{CRUMB[0]}" cy="{CRUMB[1]}" r="{CRUMB[2]}" fill="{g}"/>')
    # The vessel, the bead and the moving arc sit 12 low against the ring's optical centre.
    o.append('<g transform="translate(0,-12)">')
    if simplified:
        o.append(f'<path d="M 138 196 A 174.3 174.3 0 0 1 374 196" fill="none" stroke="{ACC}" '
                 f'stroke-width="34" stroke-linecap="round"/>')
    else:
        o.append(f'<g fill="none" stroke="{ACC}" stroke-width="34" stroke-linecap="round">'
                 f'<path d="M 138 196 A 174.3 174.3 0 0 1 332.4 167.7"/>'
                 f'<path d="M 350.9 178.1 A 174.3 174.3 0 0 1 374 196"/></g>')
    o.append(f'<path d="M 142 256 L 256 390.2 L 370 256" fill="none" stroke="{g}" stroke-width="34" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<circle cx="256" cy="300" r="36" fill="{g}"/>')
    o.append('</g>')
    return "".join(o)

def mark(x, y, px, sfx, simplified=False):
    """The mark placed at (x, y), px × px, with its own gradient id."""
    return (f'<defs>{defs(sfx)}</defs>'
            f'<g transform="translate({x},{y}) scale({px/512:.6f})">{body(sfx, simplified)}</g>')

def tile(size, sfx, simplified=False, pad=0.0):
    """The full square asset: ground, glow, hairline, mark."""
    k = size / 512
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
<defs>{defs(sfx)}
<radialGradient id="gl{sfx}" cx="0.5" cy="0.32" r="0.72">
<stop offset="0" stop-color="{MINT}" stop-opacity="0.22"/><stop offset="1" stop-color="{MINT}" stop-opacity="0"/>
</radialGradient></defs>
<rect width="{size}" height="{size}" rx="{112*k:.2f}" fill="{BG}"/>
<rect width="{size}" height="{size}" rx="{112*k:.2f}" fill="url(#gl{sfx})"/>
<rect x="{1.5*k:.2f}" y="{1.5*k:.2f}" width="{size-3*k:.2f}" height="{size-3*k:.2f}" rx="{110.5*k:.2f}"
      fill="none" stroke="{ACC}" stroke-opacity="0.28" stroke-width="{3*k:.2f}"/>
<g transform="scale({k*(1-pad):.6f}) translate({256*pad/(1-pad):.3f},{256*pad/(1-pad):.3f})">{body(sfx, simplified)}</g>
</svg>'''
