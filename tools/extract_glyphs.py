"""Convert the bundled OFL fonts into assets/glyphs.json.

The profile SVGs are shown on GitHub as <img>, where web fonts are unreliable,
so every piece of text is drawn as vector outlines. This dev-only script turns
each font into outline paths, advance widths and pair kerning. The daily build
reads the JSON and needs nothing beyond the Python standard library.

    pip install fonttools uharfbuzz
    python tools/extract_glyphs.py
"""
import itertools
import json
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = {
    # id: (file, what it is used for)
    "title": ("Anton-Regular.ttf", "the chrome name, like the game's splash title"),
    "fire": ("LuckiestGuy-Regular.ttf", "fire-gradient section titles, like the promo art"),
    "pixel": ("Silkscreen-Bold.ttf", "red pixel counters and the version stamp"),
    "ui": ("ChakraPetch-SemiBold.ttf", "body text and labels"),
    "uib": ("ChakraPetch-Bold.ttf", "numbers and emphasis"),
    "uim": ("ChakraPetch-Medium.ttf", "captions"),
}
CHARSET = [chr(c) for c in range(32, 127)] + list("·—–’‘“”•×→←°…★")


def fmt(v):
    v = round(v)
    return str(int(v))


def glyph_path(glyphset, name):
    pen = SVGPathPen(glyphset, ntos=fmt)
    glyphset[name].draw(TransformPen(pen, (1, 0, 0, 1, 0, 0)))
    return pen.getCommands()


def kerning(path, chars, cmap):
    blob = hb.Blob.from_file_path(str(path))
    font = hb.Font(hb.Face(blob))
    upm = font.face.upem
    font.scale = (upm, upm)
    present = [c for c in chars if ord(c) in cmap and c != " "]
    kern = {}
    for a, b in itertools.product(present, repeat=2):
        buf = hb.Buffer()
        buf.add_str(a + b)
        buf.guess_segment_properties()
        hb.shape(font, buf, {"kern": True, "liga": False})
        if len(buf.glyph_positions) != 2:
            continue
        single = hb.Buffer()
        single.add_str(a)
        single.guess_segment_properties()
        hb.shape(font, single, {"kern": True, "liga": False})
        delta = buf.glyph_positions[0].x_advance - single.glyph_positions[0].x_advance
        if delta:
            kern[a + b] = delta
    return kern


def main():
    out = {}
    for fid, (fname, _) in FONTS.items():
        path = ROOT / "assets" / "fonts" / fname
        tt = TTFont(path)
        cmap = tt.getBestCmap()
        gs = tt.getGlyphSet()
        os2 = tt["OS/2"]
        glyphs = {}
        for ch in CHARSET:
            name = cmap.get(ord(ch))
            if name is None:
                continue
            glyphs[ch] = [gs[name].width, glyph_path(gs, name)]
        out[fid] = {
            "file": fname,
            "upm": tt["head"].unitsPerEm,
            "cap": getattr(os2, "sCapHeight", 0) or int(0.7 * tt["head"].unitsPerEm),
            "xh": getattr(os2, "sxHeight", 0) or int(0.5 * tt["head"].unitsPerEm),
            "glyphs": glyphs,
            "kern": kerning(path, CHARSET, cmap),
        }
        print(f"{fid}: {len(glyphs)} glyphs, {len(out[fid]['kern'])} kerning pairs")
    dest = ROOT / "assets" / "glyphs.json"
    dest.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {dest} ({dest.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
