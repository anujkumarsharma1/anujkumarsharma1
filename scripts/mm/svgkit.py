"""SVG building blocks: outline text, escaping, number formatting, theme tokens.

Text is drawn from glyph outlines (assets/glyphs.json) instead of <text>, so
it renders identically wherever GitHub shows the image, with no font loading.
"""
import json
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]

# Theme tokens, sampled from the look of Mini Militia's splash screen: violet
# dusk, jungle green, fire orange, chrome, and the in-game HUD's health (green)
# and jetpack fuel (blue) bars.
C = {
    "bg": "#141126",
    "panel": "#1b1830",
    "panel2": "#231f3b",
    "panel3": "#2c2748",
    "line": "#342e55",
    "line2": "#4a4378",
    "ink": "#f4f1fb",
    "ink2": "#cdc6e4",
    "ink3": "#9a92bc",
    "olive": "#5a6a3a",
    "sand": "#d9c48a",
    "hp": "#4fd13f",
    "jet": "#2f8cff",
    "ammo": "#ffc21a",
    "alert": "#ff3b2f",
    "flame": "#ff7a1a",
    "out": "#0b0a10",
}

# Contribution cells sit in khaki dirt, like the game's ground: a pit for
# empty days, then one green hue getting darker as the count grows.
HEAT = ["#7b7364", "#b9de86", "#7cc152", "#3f9535", "#1d5f22"]

PREFIX = {"title": "t", "fire": "f", "pixel": "p", "ui": "u", "uib": "b", "uim": "m"}

REDUCED_MOTION = (
    "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
)


@lru_cache(maxsize=1)
def _glyph_data():
    return json.loads((ROOT / "assets" / "glyphs.json").read_text(encoding="utf-8"))


class Font:
    def __init__(self, fid):
        spec = _glyph_data()[fid]
        self.id = fid
        self.prefix = PREFIX[fid]
        self.upm = spec["upm"]
        self.cap = spec["cap"]
        self.glyphs = spec["glyphs"]
        self.kern = spec["kern"]

    def has(self, ch):
        return ch in self.glyphs

    def clean(self, text):
        """Replace characters the font cannot draw."""
        repl = {"’": "'", "‘": "'", "“": '"', "”": '"'}
        out = []
        for ch in text:
            ch = repl.get(ch, ch) if not self.has(ch) else ch
            out.append(ch if self.has(ch) else "?")
        return "".join(out)

    def layout(self, text, size, track=0.0):
        """Return [(char, x_px, advance_px)] and total width in px."""
        k = size / self.upm
        track_u = track * self.upm
        x = 0.0
        out = []
        prev = None
        for ch in self.clean(text):
            if prev is not None:
                x += self.kern.get(prev + ch, 0) + track_u
            adv = self.glyphs[ch][0]
            out.append((ch, x * k, adv * k))
            x += adv
            prev = ch
        return out, x * k

    def width(self, text, size, track=0.0):
        return self.layout(text, size, track)[1]


@lru_cache(maxsize=None)
def font(fid):
    return Font(fid)


def fmt_int(n):
    return f"{int(n):,}"


def compact(n):
    n = int(n)
    if n >= 100_000:
        return f"{n / 1000:.0f}K"
    if n >= 10_000:
        return f"{n / 1000:.1f}K".replace(".0K", "K")
    return f"{n:,}"


def attr(v):
    return escape(str(v), {'"': "&quot;"})


class Svg:
    """Collects markup, glyph definitions and CSS for one SVG document."""

    def __init__(self, w, h, title, desc=""):
        self.w, self.h = w, h
        self.title, self.desc = title, desc
        self.defs = []
        self.css = [REDUCED_MOTION]
        self.parts = []
        self._glyphs = {}
        self._paints = set()
        self._uid = 0

    def paint(self, name):
        """Shared gradients and filters, added to <defs> on first use."""
        if name not in self._paints:
            self._paints.add(name)
            self.defs.append(PAINTS[name])
        return f"url(#{name})"

    def uid(self, prefix="i"):
        self._uid += 1
        return f"{prefix}{self._uid}"

    def add(self, *markup):
        self.parts.extend(m for m in markup if m)

    def style(self, css):
        self.css.append(css)

    def _use(self, f, ch, x_units):
        if ch == " ":
            return ""
        self._glyphs.setdefault(f.id, set()).add(ch)
        xs = f"{x_units:.0f}"
        return f'<use href="#{f.prefix}{ord(ch):x}"' + (f' x="{xs}"' if xs != "0" else "") + "/>"

    def text(self, s, x, y, fnt="ui", size=14, fill=None, anchor="start", track=0.0,
             stroke=None, sw=0.0, cls=None, style=None, opacity=None, max_width=None):
        """Draw one line of text with its baseline at y. Returns the markup."""
        f = font(fnt)
        if max_width is not None:
            s = fit(s, fnt, size, max_width, track)
        glyphs, width = f.layout(s, size, track)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        k = size / f.upm
        uses = "".join(self._use(f, ch, gx / k) for ch, gx, _ in glyphs)
        a = [f'transform="translate({x:.1f} {y:.1f}) scale({k:.5f} {-k:.5f})"']
        a.append(f'fill="{fill or C["ink"]}"')
        if stroke:
            a.append(f'stroke="{stroke}" stroke-width="{sw / k:.0f}" paint-order="stroke" '
                     'stroke-linejoin="round"')
        if cls:
            a.append(f'class="{cls}"')
        if style:
            a.append(f'style="{style}"')
        if opacity is not None:
            a.append(f'opacity="{opacity}"')
        return f"<g {' '.join(a)}>{uses}</g>"

    def letters(self, s, x, y, fnt="ui", size=14, anchor="start", track=0.0):
        """Per-letter placement for letter-by-letter animation.

        Returns [(char, x_px, advance_px, markup)], where markup draws the
        glyph at its final position with its baseline at y.
        """
        f = font(fnt)
        glyphs, width = f.layout(s, size, track)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        k = size / f.upm
        out = []
        for ch, gx, adv in glyphs:
            if ch == " ":
                continue
            use = self._use(f, ch, 0)
            mk = f'<g transform="translate({x + gx:.1f} {y:.1f}) scale({k:.5f} {-k:.5f})">{use}</g>'
            out.append((ch, x + gx, adv, mk))
        return out

    def render(self):
        data = _glyph_data()
        glyph_defs = []
        for fid, chars in sorted(self._glyphs.items()):
            f = font(fid)
            for ch in sorted(chars):
                d = data[fid]["glyphs"][ch][1]
                if d:
                    glyph_defs.append(f'<path id="{f.prefix}{ord(ch):x}" d="{d}"/>')
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>'
        )
        defs = "<defs>" + "".join(glyph_defs) + "".join(self.defs) + "</defs>"
        css = "<style>" + "".join(self.css) + "</style>"
        return head + defs + css + "".join(self.parts) + "</svg>"


def fit(s, fnt, size, max_width, track=0.0):
    """Truncate with an ellipsis so the text fits max_width."""
    f = font(fnt)
    if f.width(s, size, track) <= max_width:
        return s
    ell = "…" if f.has("…") else "..."
    while s and f.width(s + ell, size, track) > max_width:
        s = s[:-1]
    return s.rstrip() + ell


def wrap(s, fnt, size, max_width, max_lines=None, track=0.0):
    """Greedy word wrap. The last allowed line is truncated with an ellipsis."""
    f = font(fnt)
    words = s.split()
    lines, cur = [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if f.width(cand, size, track) <= max_width or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = fit(lines[-1] + " …", fnt, size, max_width, track)
    return [fit(line, fnt, size, max_width, track) for line in lines]


def panel(svg, x, y, w, h, r=16, fill=None, stroke=None):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
            f'fill="{fill or C["panel"]}" stroke="{stroke or C["line"]}" stroke-width="1.5"/>')


def header(svg, title, right=None, y=27, w=None, x=22):
    """Panel title strip: fire-lettered title on the left, caption on the right."""
    w = w or svg.w
    out = [fire_text(svg, title, x, y, 19)]
    if right:
        out.append(svg.text(right, w - 22, y - 2, "uim", 11.5, C["ink3"], anchor="end",
                            track=0.04, max_width=w - 280))
    out.append(f'<rect x="{x}" y="{y + 10}" width="{w - 2 * x}" height="1" fill="{C["line"]}"/>')
    return "".join(out)


def fire_text(svg, s, x, y, size, anchor="start", track=0.02):
    """Fire-gradient lettering with a black outline and drop shadow."""
    shadow = svg.text(s, x + size * 0.06, y + size * 0.08, "fire", size, "#000", anchor=anchor,
                      track=track, opacity=".55")
    main = svg.text(s, x, y, "fire", size, svg.paint("fire"), anchor=anchor, track=track,
                    stroke=C["out"], sw=size * 0.09)
    return shadow + main


def chrome_text(svg, s, x, y, size, anchor="start", track=0.02, glow=True):
    """Chrome lettering with a dark outline and an orange rim glow."""
    shadow = svg.text(s, x + size * 0.05, y + size * 0.07, "title", size, "#000", anchor=anchor,
                      track=track, opacity=".5")
    main = svg.text(s, x, y, "title", size, svg.paint("chrome"), anchor=anchor, track=track,
                    stroke="#111018", sw=size * 0.06)
    if glow:
        main = f'<g filter="{svg.paint("rimglow")}">{main}</g>'
    return shadow + main


PAINTS = {
    "chrome": '<linearGradient id="chrome" x1="0" y1="0" x2="0" y2="1">'
              '<stop offset="0" stop-color="#ffffff"/><stop offset=".42" stop-color="#d9dde2"/>'
              '<stop offset=".5" stop-color="#6f757d"/><stop offset=".62" stop-color="#abb1b8"/>'
              '<stop offset=".86" stop-color="#eef1f3"/><stop offset="1" stop-color="#8d939a"/>'
              '</linearGradient>',
    "fire": '<linearGradient id="fire" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#fff04a"/><stop offset=".45" stop-color="#ffb21a"/>'
            '<stop offset=".8" stop-color="#ff5a14"/><stop offset="1" stop-color="#d8231a"/>'
            '</linearGradient>',
    "rimglow": '<filter id="rimglow" x="-10%" y="-40%" width="120%" height="180%">'
               '<feGaussianBlur stdDeviation="2.6" result="b"/><feFlood flood-color="#ff7a1a"/>'
               '<feComposite in2="b" operator="in"/>'
               '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    "camo": '<pattern id="camo" width="24" height="24" patternUnits="userSpaceOnUse">'
            '<rect width="24" height="24" fill="#6b7b43"/>'
            '<path d="M2,3 q5,-3 8,1 q2,4 -3,5 q-5,1 -5,-6z" fill="#3b4a25"/>'
            '<path d="M13,1 q6,0 7,4 q-2,3 -7,1z" fill="#7b5a36"/>'
            '<path d="M14,11 q6,-2 8,3 q1,5 -5,5 q-5,-1 -3,-8z" fill="#3b4a25"/>'
            '<path d="M3,14 q4,-1 5,3 q-1,3 -5,2z" fill="#262a1c"/>'
            '<path d="M8,19 q4,-2 6,1 q-1,4 -6,3z" fill="#7b5a36"/>'
            '<path d="M18,6 q3,1 2,3 q-2,1 -3,-1z" fill="#262a1c"/>'
            '</pattern>',
}
