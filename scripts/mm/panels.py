"""Every panel of the profile, each rendered as a standalone animated SVG.

The look follows Mini Militia (Doodle Army 2): the violet-dusk jungle splash,
chrome and fire lettering, the in-game HUD frame with heart and jetpack-fuel
bars, khaki dirt with a grass edge, and doodle soldiers with boot jets.
"""
import datetime as dt
import math
import random

from . import art
from .data import ago, languages, rank, streaks
from .svgkit import C, HEAT, Svg, chrome_text, compact, fire_text, fmt_int, font, header, wrap

W = 840
CUT = 16


# ------------------------------------------------------------------ frames

def _shape(w, h, cut=CUT, inset=0.0):
    i = inset
    return f"M{i},{i} H{w - i} V{h - cut - i * 0.4:.1f} L{w - cut - i * 0.4:.1f},{h - i} H{i} Z"


def _frame(svg, fill=None, cut=CUT):
    """Panel background in the game's HUD shape (cut bottom-right corner)."""
    cid = svg.uid("clip")
    svg.defs.append(f'<clipPath id="{cid}"><path d="{_shape(svg.w, svg.h, cut)}"/></clipPath>')
    svg.add(f'<path d="{_shape(svg.w, svg.h, cut)}" fill="{fill or C["panel"]}"/>')
    return cid


def _border(svg, cut=CUT):
    """Double light border, like the in-game HUD frame."""
    svg.add(f'<path d="{_shape(svg.w, svg.h, cut, 1.5)}" fill="none" stroke="#f1eefa" '
            'stroke-opacity=".42" stroke-width="3"/>'
            f'<path d="{_shape(svg.w, svg.h, cut, 6)}" fill="none" stroke="#f1eefa" '
            'stroke-opacity=".13" stroke-width="1.2"/>')


def _tile_shape(x, y, w, h, cut=9):
    return f"M{x},{y} H{x + w} V{y + h - cut} L{x + w - cut},{y + h} H{x} Z"


def local_time(now, cfg):
    try:
        from zoneinfo import ZoneInfo
        t = now.astimezone(ZoneInfo(cfg.get("timezone", "UTC")))
        return t, t.tzname() or "UTC"
    except Exception:  # zoneinfo data missing: fall back to UTC
        return now, "UTC"


# ------------------------------------------------------------------- hero

def _jungle(side_seed, flip=False):
    """A cluster of fronds and leaves hanging in from one side of the frame."""
    rnd = random.Random(side_seed)
    parts = [
        art.frond(-40, 18, 200, 22 + rnd.uniform(-6, 6), 0.3, 10, art.LEAF_DARK),
        art.frond(-46, 128, 185, 4 + rnd.uniform(-6, 6), 0.26, 9, art.LEAF),
        art.leaf(-18, 222, 128, -18 + rnd.uniform(-6, 6), 0.36, art.LEAF),
        art.frond(-40, 300, 170, -34 + rnd.uniform(-6, 6), 0.3, 9, art.LEAF_DARK),
        art.leaf(-12, 76, 104, 26, 0.38, art.LEAF_LIGHT),
        art.leaf(4, 170, 96, 8, 0.4, art.LEAF_DARK, veins=3),
    ]
    g = "".join(parts)
    if flip:
        g = f'<g transform="translate({W} 0) scale(-1 1)">{g}</g>'
    return g


def hero(snap, cfg, now):
    g = snap["github"]
    H = 340
    svg = Svg(W, H, f"{cfg['display_name']} — {cfg['headline']}",
              "Animated splash screen in the style of Mini Militia: a jetpack soldier rises out of "
              "the jungle and shoots the name onto the screen with two pistols.")
    clip = _frame(svg, fill="#2e3160")
    svg.defs.append('<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
                    '<stop offset="0" stop-color="#6e53a3"/><stop offset=".55" stop-color="#58498e"/>'
                    '<stop offset="1" stop-color="#2f3162"/></linearGradient>'
                    '<radialGradient id="burn" cx=".5" cy=".5" r=".5">'
                    '<stop offset="0" stop-color="#ffb347" stop-opacity=".95"/>'
                    '<stop offset=".35" stop-color="#ff7a1a" stop-opacity=".55"/>'
                    '<stop offset="1" stop-color="#ff5a14" stop-opacity="0"/></radialGradient>')
    svg.add(f'<g clip-path="url(#{clip})">',
            f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
            '<path d="M0,262 L110,214 L220,250 L350,196 L500,246 L640,202 L760,246 L840,220 V340 H0 Z" fill="#4b4a86"/>',
            '<path d="M0,300 L150,256 L300,292 L460,246 L600,288 L740,250 L840,282 V340 H0 Z" fill="#393a72"/>',
            '<ellipse cx="420" cy="336" rx="320" ry="130" fill="url(#burn)" class="burn"/>',
            f'<g class="swayL">{_jungle(5)}</g>',
            f'<g class="swayR">{_jungle(9, flip=True)}</g>',
            art.bushes(W, 318, seed=4, colour="#07080c"),
            "</g>")

    # ---- the name: chrome letters, shot in from the middle outward
    px, py, sc = 420.0, 224.0, 1.1
    size, base = 64, 86
    tf = font("title")
    k = size / tf.upm
    cap = tf.cap * k
    letters = svg.letters(cfg["display_name"].upper(), W / 2, base, "title", size, anchor="middle",
                          track=0.03)
    left = sorted([l for l in letters if l[1] + l[2] / 2 < W / 2], key=lambda l: -l[1])
    right = sorted([l for l in letters if l[1] + l[2] / 2 >= W / 2], key=lambda l: l[1])
    order = []
    for i in range(max(len(left), len(right))):
        if i < len(right):
            order.append((1, right[i]))
        if i < len(left):
            order.append((-1, left[i]))
    t0, gap = 1.15, 0.11
    arms = {-1: [(0.0, -28.0), (1.0, -28.0)], 1: [(0.0, -28.0), (1.0, -28.0)]}
    shadows, mains, fx = [], [], []
    for i, (side, (ch, lx, adv, mk)) in enumerate(order):
        t = t0 + i * gap
        tx, ty = lx + adv / 2, base - cap / 2
        ang = art.front_aim(px, py, sc, side, tx, ty)
        mx, my = art.front_muzzle(px, py, sc, side, ang)
        arms[side] += [(t - 0.05, ang), (t + 0.05, ang - 7)]
        d = f"animation-delay:{t + 0.05:.2f}s"
        shadows.append(f'<g class="pop" style="{d}"><g transform="translate(3 4)">{mk}</g></g>')
        mains.append(f'<g class="pop" style="{d}">{mk}</g>')
        fx.append(art.streak(svg, mx, my, tx, ty, 5.5, 1.4, "shot", f"animation-delay:{t:.2f}s"))
        fx.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="7" fill="#fff3a0" class="mfx" '
                  f'style="animation-delay:{t:.2f}s"/>')
        fx.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="12" fill="#ffd166" class="hit" '
                  f'style="animation-delay:{t + 0.04:.2f}s"/>')
    t_end = t0 + len(order) * gap
    for side in (-1, 1):
        arms[side] += [(t_end + 0.1, arms[side][-1][1]), (t_end + 0.45, -28.0), (3.6, -28.0)]
    svg.add(f'<g fill="#000" opacity=".5">{"".join(shadows)}</g>',
            f'<g filter="{svg.paint("rimglow")}"><g fill="{svg.paint("chrome")}" stroke="#111018" '
            f'stroke-width="{3.4 / k:.0f}" paint-order="stroke" stroke-linejoin="round">{"".join(mains)}</g></g>')

    # ---- headline, typed in
    hy = 116
    hw = font("fire").width(cfg["headline"].upper(), 16, 0.04)
    svg.defs.append(f'<clipPath id="hl"><rect class="wipe" x="{W / 2 - hw / 2 - 4:.0f}" y="{hy - 18}" '
                    f'width="{hw + 8:.0f}" height="26"/></clipPath>')
    svg.add(f'<g clip-path="url(#hl)">'
            + svg.text(cfg["headline"].upper(), W / 2 + 1.5, hy + 2, "fire", 16, "#000", anchor="middle",
                       track=0.04, opacity=".6")
            + svg.text(cfg["headline"].upper(), W / 2, hy, "fire", 16, "#ffffff", anchor="middle",
                       track=0.04, stroke=C["out"], sw=2.2) + "</g>")

    # ---- the soldier
    svg.add(f'<g class="pilot"><g class="bob"><g transform="scale({sc})">'
            + art.soldier_front(svg, flash_cls=None) + "</g></g></g>")
    svg.add(*fx)

    # ---- HUD frames: objective (left) and dossier (right)
    obj = cfg.get("objective")
    if obj:
        svg.add('<g class="hudL">' + art.hud_frame(22, 150, 238, 90)
                + fire_text(svg, "OBJECTIVE", 38, 178, 15)
                + "".join(svg.text(line, 38, 200 + i * 18, "ui", 13, C["ink"])
                          for i, line in enumerate(wrap(obj, "ui", 13, 206, max_lines=2)))
                + "</g>")
    chips = cfg.get("chips", [])[:3]
    if chips:
        rows = "".join(art.icon("bullet", 598, 164 + i * 22, 14, C["ammo"])
                       + svg.text(c, 618, 176 + i * 22, "uib", 12, C["ink"], track=0.08, max_width=180)
                       for i, c in enumerate(chips))
        svg.add(f'<g class="hudR">{art.hud_frame(580, 150, 238, 90)}{rows}</g>')

    since = dt.datetime.fromisoformat(g["created_at"].replace("Z", "+00:00"))
    stamp = local_time(now, cfg)[0].strftime("%Y.%m.%d")
    svg.add(svg.text(f"IN THE FIELD SINCE {since.strftime('%b %Y').upper()}", 22, 330, "pixel", 9,
                     C["ink2"], track=0.06),
            svg.text(f"V{stamp}", W - 26, 331, "pixel", 11, "#d7d3e6", anchor="end", track=0.1))

    T = 3.6

    def kf(frames):
        return "".join(f"{min(100, max(0, t / T * 100)):.2f}%{{transform:rotate({a:.1f}deg)}}"
                       for t, a in sorted(frames))
    svg.style(
        ".burn{animation:burn 1.8s ease-in-out infinite alternate}"
        "@keyframes burn{from{opacity:.75}to{opacity:1}}"
        ".swayL{transform-origin:0 170px;animation:sway 6s ease-in-out infinite alternate}"
        f".swayR{{transform-origin:{W}px 170px;animation:sway 7s ease-in-out -2s infinite alternate-reverse}}"
        "@keyframes sway{from{transform:rotate(-1.6deg)}to{transform:rotate(1.4deg)}}"
        f".pilot{{transform:translate({px}px,{py}px);animation:rise 1.05s cubic-bezier(.2,.8,.3,1) both}}"
        f"@keyframes rise{{from{{transform:translate({px}px,430px)}}to{{transform:translate({px}px,{py}px)}}}}"
        ".bob{animation:bob 2.6s ease-in-out 3.6s infinite}"
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}"
        ".flame{animation:fl .14s ease-in-out infinite alternate}"
        "@keyframes fl{from{transform:scale(1,1)}to{transform:scale(.84,.7)}}"
        f".armL{{transform:rotate(-28deg);animation:aimL {T}s linear both}}"
        f".armR{{transform:rotate(-28deg);animation:aimR {T}s linear both}}"
        f"@keyframes aimL{{{kf(arms[-1])}}}@keyframes aimR{{{kf(arms[1])}}}"
        ".shot{opacity:0;animation:shot .13s linear forwards}"
        "@keyframes shot{0%{opacity:1}70%{opacity:.9}100%{opacity:0}}"
        ".mfx{opacity:0;transform-box:fill-box;transform-origin:center;animation:hit .16s ease-out both}"
        ".hit{opacity:0;transform-box:fill-box;transform-origin:center;animation:hit .32s ease-out both}"
        "@keyframes hit{0%{opacity:0;transform:scale(.2)}15%{opacity:.95}100%{opacity:0;transform:scale(2.2)}}"
        ".pop{transform-box:fill-box;transform-origin:center;animation:pop .24s cubic-bezier(.3,1.6,.5,1) both}"
        "@keyframes pop{0%{opacity:0;transform:scale(1.8) rotate(-8deg)}100%{opacity:1;transform:none}}"
        ".wipe{transform-box:fill-box;transform-origin:0 50%;animation:wipe .7s steps(30) 3.05s both}"
        "@keyframes wipe{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        ".hudL{animation:inL .5s ease-out 3.4s both}.hudR{animation:inR .5s ease-out 3.55s both}"
        "@keyframes inL{from{opacity:0;transform:translateX(-40px)}to{opacity:1;transform:none}}"
        "@keyframes inR{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:none}}"
    )
    _border(svg)
    return svg


# ------------------------------------------------------------- comms buttons

COMMS = {
    # key: (label, action, plate colour, brand mark)
    "linkedin": ("LINKEDIN", "CONNECT", "#0a66c2", "linkedin"),
    "email": ("GMAIL", "EMAIL ME", "#c5362b", "gmail"),
    "codeforces": ("CODEFORCES", "PROFILE", "#1b2430", "codeforces"),
    "topmate": ("TOPMATE", "BOOK A CALL", "#5a4a2a", "topmate"),
    "x": ("X / TWITTER", "FOLLOW", "#000000", "x"),
    "medium": ("MEDIUM", "READ", "#111111", "medium"),
}


def comms_button(key, channel):
    label, action, plate, mark = COMMS[key]
    w, h = 132, 46
    svg = Svg(w, h, f"{label.title()} — {action.lower()}", f"Contact button: {label}")
    cid = svg.uid("b")
    shape = _tile_shape(0, 0, w, h, 10)
    svg.defs.append(f'<clipPath id="{cid}"><path d="{shape}"/></clipPath>'
                    '<linearGradient id="gl" x1="0" y1="0" x2="1" y2="0">'
                    '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                    '<stop offset=".5" stop-color="#fff" stop-opacity=".18"/>'
                    '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    svg.add(f'<path d="{shape}" fill="{C["panel2"]}"/>',
            f'<path d="{_tile_shape(1.5, 1.5, w - 3, h - 3, 9)}" fill="none" stroke="#f1eefa" '
            'stroke-opacity=".45" stroke-width="2"/>',
            f'<rect x="8" y="8" width="30" height="30" rx="6" fill="{plate}" stroke="#ffffff30"/>',
            art.brand(mark, 13, 13, 20, "#fff"),
            svg.text(label, 46, 24, "fire", 12.5, "#fff", track=0.04, max_width=w - 52,
                     stroke=C["out"], sw=1.6),
            svg.text(action, 46, 37, "uim", 9, C["ink2"], track=0.1, max_width=w - 52),
            f'<g clip-path="url(#{cid})"><rect class="glint" x="-60" y="-10" width="46" height="70" '
            'fill="url(#gl)"/></g>')
    svg.style(f".glint{{animation:gl 7s ease-in-out {channel * 0.35:.2f}s infinite}}"
              "@keyframes gl{0%{transform:translateX(0) skewX(-20deg)}"
              "22%,100%{transform:translateX(250px) skewX(-20deg)}}")
    return svg


# --------------------------------------------------------------- player card

def _tile(svg, x, y, w, h, icon, colour, label, value, caption):
    return (f'<path d="{_tile_shape(x, y, w, h)}" fill="{C["panel2"]}" stroke="#f1eefa" '
            'stroke-opacity=".16" stroke-width="1.2"/>'
            + art.icon(icon, x + w - 27, y + 12, 15, colour)
            + svg.text(value, x + 12, y + 42, "uib", 28, C["ink"], max_width=w - 44)
            + svg.text(label, x + 12, y + 62, "uib", 10, C["ink2"], track=0.06, max_width=w - 20)
            + svg.text(caption, x + 12, y + 76, "uim", 9.5, C["ink3"], track=0.02, max_width=w - 20))


def player_card(snap, cfg, now):
    g = snap["github"]
    t, tz = local_time(now, cfg)
    cur, longest = streaks(g["daily"], t.date())
    active = sum(1 for w in g["calendar"] for d in w if d["count"] > 0)
    xp = g["contributions_all_time"]
    idx, rname, prog, to_next, nxt = rank(xp)
    stars = sum(r["stars"] for r in g["repos"])
    H = 256
    svg = Svg(W, H, "Player card",
              f"{fmt_int(g['commits_all_time'])} commits all-time, "
              f"{fmt_int(g['contributions_last_year'])} contributions in the last 12 months, "
              f"current streak {cur} days, best {longest} days, rank {rname}.")
    _frame(svg)
    svg.add(header(svg, "PLAYER CARD", f"SYNCED {t.strftime('%d %b %Y · %H:%M').upper()} {tz}"))

    # dossier with avatar
    svg.add(art.hud_frame(20, 52, 288, 186, cut=16, opacity=0.5))
    ax, ay, asz = 36, 68, 92
    cid = svg.uid("av")
    svg.defs.append(f'<clipPath id="{cid}"><rect x="{ax}" y="{ay}" width="{asz}" height="{asz}" '
                    'rx="8"/></clipPath>')
    if g.get("avatar"):
        svg.add(f'<image href="{g["avatar"]}" x="{ax}" y="{ay}" width="{asz}" height="{asz}" '
                f'clip-path="url(#{cid})" preserveAspectRatio="xMidYMid slice"/>')
    else:
        svg.add(f'<rect x="{ax}" y="{ay}" width="{asz}" height="{asz}" rx="8" fill="#58498e"/>'
                + art.head_icon(svg, ax + asz / 2, ay + asz / 2 + 6, 86))
    svg.add(f'<rect x="{ax}" y="{ay}" width="{asz}" height="{asz}" rx="8" fill="none" '
            f'stroke="{C["olive"]}" stroke-width="3"/>')
    since = dt.datetime.fromisoformat(g["created_at"].replace("Z", "+00:00"))
    svg.add(svg.text(cfg["display_name"], 142, 88, "uib", 15.5, C["ink"], max_width=156),
            svg.text("@" + g["login"], 142, 106, "uim", 11.5, C["ink3"], max_width=156),
            svg.text(f"ENLISTED {since.strftime('%b %Y').upper()}", 142, 130, "pixel", 9, C["ink2"],
                     track=0.04),
            svg.text(f"{fmt_int(g['followers'])} FOLLOWERS", 142, 146, "pixel", 9, C["ink2"],
                     track=0.04))
    svg.add(art.insignia(idx, 32, 172),
            fire_text(svg, rname, 78, 188, 17),
            svg.text(f"RANK {idx + 1:02d}/10 · {fmt_int(xp)} XP", 78, 203, "uim", 10, C["ink3"],
                     track=0.08))
    bw = 254
    svg.add(f'<rect x="36" y="212" width="{bw}" height="8" fill="#0a0913" stroke="#f1eefa" '
            'stroke-opacity=".35"/>',
            f'<rect x="36" y="212" width="{max(6, bw * prog):.1f}" height="8" fill="{C["ammo"]}" class="xp"/>')
    note = f"{fmt_int(to_next)} XP TO {nxt}" if nxt else "MAX RANK"
    svg.add(svg.text("XP = ALL-TIME CONTRIBUTIONS", 36, 229, "uim", 8.5, C["ink3"], track=0.06),
            svg.text(note, 290, 229, "uim", 8.5, C["ink2"], anchor="end", track=0.06))

    tiles = [
        ("bullet", C["ammo"], "COMMITS", compact(g["commits_all_time"]), "all-time, public"),
        ("crate", C["hp"], "CONTRIBUTIONS", compact(g["contributions_last_year"]), "last 12 months"),
        ("calendar", C["jet"], "ACTIVE DAYS", fmt_int(active), "of the last 365"),
        ("flame", C["flame"], "STREAK", f"{cur}", "days in a row, now"),
        ("medal", C["ammo"], "BEST STREAK", f"{longest}", "days, all-time"),
        ("merge", C["jet"], "PULL REQUESTS", compact(g["pull_requests"]), "opened, any repo"),
        ("repo", C["hp"], "PUBLIC REPOS", fmt_int(g["repo_count"]), "own, forks excluded"),
        ("star", C["ammo"], "STARS", fmt_int(stars), "on own repos"),
    ]
    x0, y0, tw, th, gap = 322, 52, 116.5, 88, 10
    for i, (ic, col, label, value, cap) in enumerate(tiles):
        x = x0 + (i % 4) * (tw + gap)
        y = y0 + (i // 4) * (th + gap)
        svg.add(f'<g class="tile" style="animation-delay:{0.05 * i:.2f}s">'
                + _tile(svg, x, y, tw, th, ic, col, label, value, cap) + "</g>")
    svg.style(".xp{transform-box:fill-box;transform-origin:0 50%;animation:xp 1.4s cubic-bezier(.2,.8,.2,1) .3s both}"
              "@keyframes xp{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
              ".tile{animation:tile .5s ease-out both}"
              "@keyframes tile{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}")
    _border(svg)
    return svg


# ------------------------------------------------------------------ armory

SLOTS = ["PRIMARY", "SECONDARY", "SIDEARM", "SPECIAL", "BACKUP"]


def loadout(snap, cfg):
    g = snap["github"]
    langs = languages(g["repos"], cfg.get("ignore_languages", []))
    n_repos = sum(1 for r in g["repos"] if r["languages"])
    rows = max(1, len(langs))
    H = 62 + rows * 36 + 12
    desc = ", ".join(f"{n} {s * 100:.1f}%" for n, s in langs) or "no language data"
    svg = Svg(W, H, "Armory: top languages", f"Share of code bytes: {desc}.")
    _frame(svg)
    svg.add(header(svg, "ARMORY", f"TOP LANGUAGES · SHARE OF CODE BYTES ACROSS {n_repos} REPOS"))
    taken = set()
    seg, pitch, nseg, bx = 11, 14, 30, 346
    for i, (name, share) in enumerate(langs):
        y = 56 + i * 36
        wpn = art.weapon_for(name, taken)
        taken.add(wpn)
        filled = max(1, round(share * nseg)) if share > 0 else 0
        svg.add(svg.text(SLOTS[i] if i < len(SLOTS) else f"SLOT {i + 1}", 22, y + 19, "uib", 9.5,
                         C["ink3"], track=0.12),
                art.weapon(wpn, 100, y + 5, 0.95, fill="#e4e7ea"),
                svg.text(name, 186, y + 15, "uib", 15, C["ink"], max_width=150),
                svg.text(wpn, 186, y + 29, "uim", 9.5, C["ink3"], track=0.12))
        segs = []
        for j in range(nseg):
            on = j < filled
            segs.append(f'<rect x="{bx + j * pitch}" y="{y + 7}" width="{seg}" height="17" rx="1.5" '
                        f'fill="{C["ammo"] if on else "#2a2544"}"'
                        + (f' class="ld" style="animation-delay:{0.25 + i * 0.12 + j * 0.018:.3f}s"'
                           if on else "") + "/>")
        svg.add("".join(segs))
        svg.add(svg.text(f"{share * 100:.1f}%", W - 24, y + 21, "uib", 15, C["ink"], anchor="end"))
    if not langs:
        svg.add(svg.text("NO LANGUAGE DATA YET", 22, 82, "uib", 13, C["ink3"]))
    svg.style(".ld{animation:ld .2s ease-out both}@keyframes ld{from{opacity:0}to{opacity:1}}")
    _border(svg)
    return svg


# -------------------------------------------------------------- battlefield

KILL_WEAPON = {"push": "AK47", "create": "SMAW", "pr": "M93BA", "merge": "M93BA",
               "release": "FRAG", "issue": "UZI"}


def _kill_detail(e):
    k = e["kind"]
    if k == "push":
        n = e.get("n")
        return f"PUSHED {n} COMMIT{'S' if n != 1 else ''}" if n else "PUSHED CODE"
    return {"create": "NEW REPO", "pr": f"OPENED PR #{e.get('n')}",
            "merge": f"MERGED PR #{e.get('n')}", "release": "SHIPPED A RELEASE",
            "issue": "OPENED AN ISSUE"}[k]


def _grass(x0, x1, y, seed):
    rnd = random.Random(seed)
    pts = [f"{x0},{y + 7}"]
    x = x0
    while x < x1:
        pts.append(f"{x:.0f},{y + rnd.uniform(-1, 2):.1f}")
        pts.append(f"{x + 4:.0f},{y - rnd.uniform(3, 7):.1f}")
        x += 8
    pts.append(f"{x1},{y}")
    pts.append(f"{x1},{y + 7}")
    return (f'<polygon points="{" ".join(pts)}" fill="#6aa84f" stroke="#0b0a10" stroke-width="2" '
            'stroke-linejoin="round"/>'
            f'<rect x="{x0}" y="{y + 4}" width="{x1 - x0}" height="5" fill="#3f7a31"/>')


def _pebbles(rng, box, n):
    x0, y0, x1, y1 = box
    out = []
    for _ in range(n):
        cx, cy, r = rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(3, 5.5)
        pts = " ".join(f"{cx + math.cos(a) * r * rng.uniform(.75, 1.1):.1f},"
                       f"{cy + math.sin(a) * r * .8 * rng.uniform(.75, 1.1):.1f}"
                       for a in [i * math.pi / 3 + rng.uniform(-.2, .2) for i in range(6)])
        out.append(f'<polygon points="{pts}" fill="#a49c8c" stroke="#3a352d" stroke-width="1.6"/>')
    return "".join(out)


def battlefield(snap, cfg, now):
    g = snap["github"]
    weeks = g["calendar"]
    total = g["contributions_last_year"]
    today = local_time(now, cfg)[0].date()
    cur, longest = streaks(g["daily"], today)
    active = sum(1 for w in weeks for d in w if d["count"] > 0)
    H = 306
    svg = Svg(W, H, "Battlefield: contribution graph",
              f"{fmt_int(total)} contributions in the last 12 months, shown as a Mini Militia match: "
              "a jetpack soldier flies over the calendar and blasts every day that has contributions.")
    _frame(svg)
    # header with the colour legend on the right
    svg.add(fire_text(svg, "BATTLEFIELD", 22, 27, 19))
    lx = W - 22 - 30
    svg.add(svg.text("MORE", W - 22, 25, "uim", 9, C["ink3"], anchor="end", track=0.08))
    for i, c in enumerate(reversed(HEAT)):
        svg.add(f'<rect x="{lx - 14 - i * 14}" y="16" width="11" height="11" rx="2" fill="{c}" '
                'stroke="#0b0a10" stroke-width=".8"/>')
    lx2 = lx - 14 - 4 * 14 - 6
    less_w = font("uim").width("LESS", 9, 0.08)
    svg.add(svg.text("LESS", lx2, 25, "uim", 9, C["ink3"], anchor="end", track=0.08),
            svg.text(f"{fmt_int(total)} CONTRIBUTIONS · LAST 12 MONTHS", lx2 - less_w - 18, 25, "uim", 11,
                     C["ink3"], anchor="end", track=0.04),
            f'<rect x="22" y="37" width="{W - 44}" height="1" fill="{C["line"]}"/>')

    ax0, ay0, ax1, ay1 = 16, 46, W - 16, H - 14
    aclip = svg.uid("ar")
    svg.defs.append(f'<clipPath id="{aclip}"><path d="{_tile_shape(ax0, ay0, ax1 - ax0, ay1 - ay0, 12)}"/></clipPath>'
                    '<linearGradient id="day" x1="0" y1="0" x2="0" y2="1">'
                    '<stop offset="0" stop-color="#b8cfd6"/><stop offset="1" stop-color="#e2ebe7"/></linearGradient>')
    ground_y = 160
    rng = random.Random(3)
    scene = [f'<g clip-path="url(#{aclip})">',
             f'<rect x="{ax0}" y="{ay0}" width="{ax1 - ax0}" height="{ay1 - ay0}" fill="url(#day)"/>',
             f'<path d="M{ax0},150 L120,104 L230,142 L330,96 L470,140 L600,100 L720,138 L{ax1},112 '
             f'V{ground_y} H{ax0} Z" fill="#a9bec3"/>',
             f'<path d="M{ax0},{ground_y} L60,120 L90,136 L130,112 L170,{ground_y} Z" fill="#93b485"/>',
             f'<path d="M680,{ground_y} L720,116 L752,134 L790,108 L{ax1},130 V{ground_y} Z" fill="#93b485"/>',
             f'<rect x="{ax0}" y="{ground_y}" width="{ax1 - ax0}" height="{ay1 - ground_y}" fill="#8f8778"/>',
             _pebbles(rng, (ax0 + 6, ground_y + 14, 44, ay1 - 8), 5),
             _pebbles(rng, (W - 46, ground_y + 14, ax1 - 6, ay1 - 8), 5),
             _grass(ax0, ax1, ground_y, 8),
             "</g>"]
    svg.add(*scene)

    pitch, cell = 14, 11
    cols = len(weeks)
    gw = cols * pitch - 3
    gx, gy = round((W - gw) / 2), ground_y + 16
    T = 22.0
    v = (W + 140) / 15.0
    t_in, x_start, lead = 0.6, -60.0, 64.0
    sc, base_y, amp, period = 0.58, 112.0, 6.0, 2.4

    def pos(t):
        return x_start + v * (t - t_in), base_y + amp * math.sin(2 * math.pi * t / period)

    static, alive, fx, col_css, shots = [], [], [], [], []
    month_seen, last_label_x = set(), -99
    for wi, week in enumerate(weeks):
        x = gx + wi * pitch
        live = []
        for d in week:
            day = dt.date.fromisoformat(d["date"])
            row = (day.weekday() + 1) % 7
            y = gy + row * pitch
            lvl = d["level"] if d["count"] else 0
            if lvl == 0:
                static.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                              f'fill="{HEAT[0]}"/><rect x="{x}" y="{y}" width="{cell}" height="2" '
                              'fill="#5f584b" opacity=".6"/>')
            else:
                static.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                              f'fill="#4a3f33"/><circle cx="{x + 5.5}" cy="{y + 5.5}" r="2.4" fill="#2a221a"/>')
                live.append((row, y, lvl))
            if row == 0 and (day.day <= 7 or wi == 0):
                key = (day.year, day.month)
                if key not in month_seen and x - last_label_x > 26:
                    month_seen.add(key)
                    last_label_x = x
                    static.append(svg.text(day.strftime("%b").upper(), x, gy + 7 * pitch + 11,
                                           "uib", 9, "#2f2a24", track=0.08))
        if not live:
            continue
        xc = x + cell / 2
        t_hit = t_in + (xc - lead - x_start) / v
        _, ty, _ = max(live, key=lambda r: (r[2], -r[0]))
        tx, tyc = xc, ty + cell / 2
        px_, py_ = pos(t_hit)
        ang = art.aim_angle(px_, py_, sc, 1, tx, tyc)
        mx, my = art.muzzle_world(px_, py_, sc, 1, ang)
        shots.append((t_hit, ang))
        t_resp = 19.6 + (x - gx) / max(gw, 1) * 1.6
        hp_, rp = (t_hit + 0.08) / T * 100, t_resp / T * 100
        col_css.append(f"@keyframes k{wi}{{0%,{hp_:.2f}%{{opacity:1}}{hp_ + 0.35:.2f}%,{rp:.2f}%"
                       f"{{opacity:0}}{min(rp + 1.2, 100):.2f}%,100%{{opacity:1}}}}"
                       f".c{wi}{{animation-name:k{wi}}}")
        for row, y, lvl in live:
            alive.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{HEAT[lvl]}" '
                         f'stroke="#0b0a10" stroke-opacity=".35" stroke-width=".8" class="a c{wi} r{row}"/>')
        delay = f"animation-delay:{t_hit + 0.08:.2f}s"
        fx.append(art.streak(svg, mx, my, tx, tyc, 3.6, 1, "tr", f"animation-delay:{t_hit:.2f}s"))
        fx.append(f'<g class="bx" style="{delay}"><circle cx="{tx:.1f}" cy="{tyc:.1f}" r="10" '
                  f'fill="#ff9a1a"/><circle cx="{tx:.1f}" cy="{tyc:.1f}" r="6" fill="#fff1a8"/></g>')
        for k, _dd in enumerate(range(4)):
            fx.append(f'<rect x="{tx - 1.5:.1f}" y="{tyc - 1.5:.1f}" width="3.4" height="3.4" '
                      f'fill="#3a3128" class="d{k}" style="{delay}"/>')
    svg.add(*static, *alive)

    # robot drone ahead of the soldier; he takes it out on the way past
    dx_, dy_ = 470.0, 80.0
    t_drone = t_in + (dx_ - 150 - x_start) / v
    pdx, pdy = pos(t_drone)
    dang = art.aim_angle(pdx, pdy, sc, 1, dx_, dy_)
    dmx, dmy = art.muzzle_world(pdx, pdy, sc, 1, dang)
    svg.add(f'<g class="dr">{art.drone(dx_, dy_, 0.6, "drb")}</g>')
    fx.append(art.streak(svg, dmx, dmy, dx_, dy_, 3.6, 1, "tr", f"animation-delay:{t_drone:.2f}s"))
    fx.append(f'<g class="boom" style="animation-delay:{t_drone + 0.08:.2f}s">'
              f'<circle cx="{dx_}" cy="{dy_}" r="22" fill="#ff7a1a"/><circle cx="{dx_}" cy="{dy_}" r="13" '
              f'fill="#ffd166"/><circle cx="{dx_}" cy="{dy_}" r="6" fill="#fff"/></g>')
    shots.append((t_drone, dang))
    shots.sort()
    svg.add(*fx)

    # stamp after the pass
    t_last = max(s[0] for s in shots) if shots else 3.0
    t_stamp = min(t_last + 0.9, 17.5)
    cx, cy = W / 2, gy + 3.5 * pitch
    title = "SECTOR CLEARED" if len(shots) > 1 else "QUIET SECTOR"
    sub = f"{fmt_int(total)} CONTRIBUTIONS · BEST STREAK {longest} DAYS"
    bw_ = max(font("fire").width(title, 26, 0.02), font("uib").width(sub, 11.5, 0.1)) + 60
    svg.add(f'<g class="stamp"><path d="{_tile_shape(cx - bw_ / 2, cy - 38, bw_, 74, 12)}" fill="#0b0a14" '
            'fill-opacity=".86" stroke="#f1eefa" stroke-opacity=".6" stroke-width="2.5"/>'
            + fire_text(svg, title, cx, cy + 2, 26, anchor="middle")
            + svg.text(sub, cx, cy + 24, "uib", 11.5, C["ink"], anchor="middle", track=0.1)
            + "</g>")
    svg.add(f'<rect x="{gx - 6}" y="{gy - 6}" width="3" height="{7 * pitch + 9}" rx="1.5" '
            f'fill="#ffffff" class="sweep"/>')

    # soldier
    svg.add(f'<g class="pilot"><g transform="scale({sc})">'
            + art.soldier(svg, arm_cls="arm", flash_cls="mf") + "</g></g>")

    # HUD: health + jetpack fuel (top-left), lives-style counter + kill feed (top-right)
    svg.add(art.hud_frame(26, 54, 200, 54),
            art.heart(40, 63, 14),
            f'<rect x="62" y="64" width="146" height="10" fill="#0b0a14" fill-opacity=".5"/>'
            f'<rect x="62" y="64" width="146" height="10" fill="{C["hp"]}"/>',
            art.jet_icon(40, 84, 14),
            f'<rect x="62" y="86" width="146" height="10" fill="#0b0a14" fill-opacity=".5"/>'
            f'<rect x="62" y="86" width="146" height="10" fill="{C["jet"]}" class="fuel"/>')
    hx = W - 30
    cnt = f"X{active}"
    cw = font("pixel").width(cnt, 20)
    svg.add(art.head_icon(svg, hx - cw - 22, 68, 30),
            svg.text(cnt, hx, 76, "pixel", 20, C["alert"], anchor="end", stroke="#0b0a10", sw=1.2),
            svg.text("DAYS ACTIVE", hx, 90, "pixel", 7.5, "#2f2a24", anchor="end", track=0.06))
    events = g.get("events") or []
    actor = cfg.get("callsign", "ANUJ")
    for i, e in enumerate(events[:3]):
        y = 98 + i * 20
        target = e["repo"].upper()
        f_ = font("uib")
        pill_w = 10 + f_.width(actor, 10.5, 0.04) + 34 + f_.width(target, 10.5, 0.04) + 10
        x0 = W - 30 - pill_w
        wpn = art.weapon(KILL_WEAPON[e["kind"]], x0 + 12 + f_.width(actor, 10.5, 0.04), y + 4, 0.4,
                         fill="#f1eefa")
        svg.add(f'<g class="kf" style="animation-delay:{0.4 + i * 0.15:.2f}s">'
                f'<rect x="{x0:.1f}" y="{y}" width="{pill_w:.1f}" height="17" rx="3" fill="#0b0a14" '
                'fill-opacity=".7"/>'
                + svg.text(actor, x0 + 10, y + 12.5, "uib", 10.5, "#f1eefa", track=0.04) + wpn
                + svg.text(target, x0 + pill_w - 10, y + 12.5, "uib", 10.5, "#ff8b7a", anchor="end",
                           track=0.04)
                + svg.text(f"{_kill_detail(e)} · {ago(e['when'], now)}", x0 - 6, y + 12, "uib", 8.5,
                           "#2f2a24", anchor="end", track=0.05)
                + "</g>")

    # keyframes
    t_out = t_in + (W + 120 - x_start) / v
    times = sorted({round(t_in + i * 0.25, 3) for i in range(int((t_out - t_in) / 0.25) + 1)}
                   | {round(s[0], 3) for s in shots})
    fly = [f"0%,{t_in / T * 100 - 0.01:.2f}%{{transform:translate({x_start:.0f}px,{base_y:.0f}px)}}"]
    for tt in times:
        x, y = pos(tt)
        fly.append(f"{tt / T * 100:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px)}}")
    fly.append(f"{min(t_out / T * 100 + 0.1, 99.9):.2f}%,100%{{transform:translate({W + 80}px,{base_y:.0f}px)}}")
    aim = ["0%{transform:rotate(35deg)}"]
    for tt, a in shots:
        aim.append(f"{max(0, (tt - 0.06)) / T * 100:.2f}%{{transform:rotate({a:.1f}deg)}}")
        aim.append(f"{(tt + 0.05) / T * 100:.2f}%{{transform:rotate({a - 4:.1f}deg)}}")
    aim.append(f"{min((t_last + 0.4) / T * 100, 99):.2f}%,100%{{transform:rotate(35deg)}}")
    t_first = shots[0][0] if shots else t_in
    ps, pe = t_stamp / T * 100, 19.3 / T * 100
    dp = (t_drone + 0.1) / T * 100
    svg.style(
        f".a{{animation-duration:{T}s;animation-iteration-count:infinite;animation-timing-function:linear}}"
        + "".join(f".r{r}{{animation-delay:{r * 0.035:.3f}s}}" for r in range(7))
        + "".join(col_css)
        + f".pilot{{transform:translate(120px,{base_y}px);animation:fly {T}s linear infinite}}"
        "@keyframes fly{" + "".join(fly) + "}"
        f".arm{{transform:rotate(35deg);animation:aim {T}s linear infinite}}"
        "@keyframes aim{" + "".join(aim) + "}"
        f".mf{{opacity:0;animation:mfw {T}s linear infinite}}"
        f"@keyframes mfw{{0%,{t_first / T * 100 - 0.2:.2f}%{{opacity:0}}"
        f"{t_first / T * 100 - 0.1:.2f}%,{(t_last + 0.1) / T * 100:.2f}%{{opacity:1}}"
        f"{(t_last + 0.15) / T * 100:.2f}%,100%{{opacity:0}}}}"
        ".flame{animation:fl .14s ease-in-out infinite alternate}"
        "@keyframes fl{from{transform:scale(1,1)}to{transform:scale(.84,.7)}}"
        ".drb{animation:hov 1.6s ease-in-out infinite alternate}"
        "@keyframes hov{from{transform:translateY(-3px)}to{transform:translateY(3px)}}"
        f".dr{{animation:dr {T}s linear infinite}}"
        f"@keyframes dr{{0%,{dp:.2f}%{{opacity:1;transform:none}}{dp + 0.3:.2f}%,{19.6 / T * 100:.2f}%"
        f"{{opacity:0;transform:translateY(-120px)}}{20.8 / T * 100:.2f}%,100%{{opacity:1;transform:none}}}}"
        f".boom{{opacity:0;transform-box:fill-box;transform-origin:center;animation:boom {T}s linear infinite backwards}}"
        "@keyframes boom{0%{opacity:0;transform:scale(.2)}.3%{opacity:1;transform:scale(.9)}"
        "2.6%{opacity:0;transform:scale(2)}100%{opacity:0}}"
        f".tr{{opacity:0;animation:tr {T}s linear infinite}}"
        "@keyframes tr{0%{opacity:1}.45%{opacity:.9}.5%,100%{opacity:0}}"
        f".bx{{opacity:0;transform-box:fill-box;transform-origin:center;animation:bx {T}s linear infinite backwards}}"
        "@keyframes bx{0%{opacity:0;transform:scale(.3)}.15%{opacity:1;transform:scale(.8)}"
        "1.8%{opacity:0;transform:scale(1.9)}100%{opacity:0}}"
        + "".join(
            f".d{k}{{opacity:0;animation:d{k} {T}s linear infinite backwards}}"
            f"@keyframes d{k}{{0%{{opacity:0}}.1%{{opacity:1;transform:translate(0,0)}}"
            f"2%{{opacity:0;transform:translate({dx * 11}px,{dy * 9 - 6}px)}}100%{{opacity:0}}}}"
            for k, (dx, dy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))))
        + f".stamp{{opacity:0;transform-box:fill-box;transform-origin:center;animation:st {T}s linear infinite}}"
        f"@keyframes st{{0%,{ps:.2f}%{{opacity:0;transform:scale(1.25)}}{ps + 1.2:.2f}%,{pe:.2f}%"
        f"{{opacity:1;transform:scale(1)}}{pe + 1:.2f}%,100%{{opacity:0;transform:scale(1)}}}}"
        f".sweep{{opacity:0;animation:sw {T}s linear infinite}}"
        f"@keyframes sw{{0%,{19.5 / T * 100:.2f}%{{opacity:0;transform:translateX(0)}}"
        f"{19.6 / T * 100:.2f}%{{opacity:.95;transform:translateX(0)}}"
        f"{21.2 / T * 100:.2f}%{{opacity:.95;transform:translateX({gw + 10}px)}}"
        f"{21.3 / T * 100:.2f}%,100%{{opacity:0;transform:translateX({gw + 10}px)}}}}"
        f".fuel{{transform-box:fill-box;transform-origin:0 50%;animation:fuel {T}s linear infinite}}"
        f"@keyframes fuel{{0%,{t_in / T * 100:.2f}%{{transform:scaleX(1)}}"
        f"{t_out / T * 100:.2f}%{{transform:scaleX(.18)}}{21.5 / T * 100:.2f}%,100%{{transform:scaleX(1)}}}}"
        ".kf{animation:kf .4s ease-out both}"
        "@keyframes kf{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:none}}"
    )
    _border(svg)
    return svg


# ----------------------------------------------------------------- missions

STATUS = {
    "complete": ("MISSION COMPLETE", C["hp"], "check"),
    "active": ("IN PROGRESS", C["ammo"], "gear"),
    "briefed": ("BRIEFED · SCAFFOLD ONLY", C["jet"], "brief"),
    "locked": ("LOCKED", C["ink3"], "lock"),
}


def _status_chip(svg, x, y, status):
    label, colour, ic = STATUS[status]
    w = font("uib").width(label, 10, 0.12) + 36
    return (f'<path d="{_tile_shape(x, y, w, 22, 7)}" fill="{colour}" fill-opacity=".16" '
            f'stroke="{colour}" stroke-opacity=".7"/>'
            + art.icon(ic, x + 9, y + 4, 14, colour)
            + svg.text(label, x + 28, y + 15, "uib", 10, C["ink"], track=0.12))


def _tags(svg, x, y, tags):
    out = []
    for t in tags:
        w = font("uib").width(t, 9.5, 0.1) + 16
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="19" rx="2" fill="{C["panel3"]}" '
                   f'stroke="#f1eefa" stroke-opacity=".18"/>'
                   + svg.text(t, x + 8, y + 13, "uib", 9.5, C["ink2"], track=0.1))
        x += w + 6
    return "".join(out)


def _repo(snap, name):
    for r in snap["github"]["repos"]:
        if r["name"].lower() == name.lower():
            return r
    return None


def mission_featured(m, snap, now, number):
    r = _repo(snap, m["repo"])
    H = 182
    svg = Svg(W, H, f"Mission: {m['title']}", m.get("blurb", ""))
    _frame(svg)
    svg.add(f'<circle cx="96" cy="88" r="62" fill="#58498e" stroke="#f1eefa" stroke-opacity=".4" stroke-width="2"/>'
            f'<circle cx="96" cy="88" r="52" fill="none" stroke="{C["hp"]}" stroke-width="3" '
            'stroke-dasharray="4 6" class="spin"/>'
            + art.head_icon(svg, 96, 94, 88)
            + svg.text(f"MISSION {number:02d}", 96, 170, "pixel", 9, C["ink2"], anchor="middle", track=0.08))
    x = 190
    svg.add(_status_chip(svg, x, 20, m["status"]),
            chrome_text(svg, m["title"], x, 80, 40, glow=False))
    if m.get("subtitle"):
        svg.add(svg.text(m["subtitle"], x, 100, "uim", 11.5, C["ink3"], track=0.04, max_width=W - x - 24))
    for i, line in enumerate(wrap(m.get("blurb", ""), "ui", 13, W - x - 26, max_lines=2)):
        svg.add(svg.text(line, x, 125 + i * 18, "ui", 13, C["ink2"]))
    svg.add(_tags(svg, x, 152, m.get("tags", [])))
    if r:
        svg.add(svg.text(f"LAST PUSH {ago(r['pushed_at'], now)}", W - 30, 166, "uim", 10, C["ink3"],
                         anchor="end", track=0.1))
    svg.style(".spin{transform-box:fill-box;transform-origin:center;animation:spin 24s linear infinite}"
              "@keyframes spin{to{transform:rotate(360deg)}}")
    _border(svg)
    return svg


def mission_card(m, snap, now):
    r = _repo(snap, m["repo"])
    w, H = 413, 154
    svg = Svg(w, H, f"Mission: {m['title']}", m.get("blurb", ""))
    _frame(svg)
    svg.add(_status_chip(svg, 18, 16, m["status"]),
            svg.text(m["title"], 18, 70, "title", 26, C["ink"], track=0.03, max_width=w - 36,
                     stroke=C["out"], sw=1.5))
    for i, line in enumerate(wrap(m.get("blurb", ""), "ui", 12.5, w - 36, max_lines=2)):
        svg.add(svg.text(line, 18, 91 + i * 17, "ui", 12.5, C["ink2"]))
    svg.add(_tags(svg, 18, 120, m.get("tags", [])))
    if r:
        svg.add(svg.text(f"LAST PUSH {ago(r['pushed_at'], now)}", w - 24, 133, "uim", 9.5, C["ink3"],
                         anchor="end", track=0.1))
    _border(svg)
    return svg


def locked_levels(ms):
    H = 122
    svg = Svg(W, H, "Locked levels", "Planned projects: " + ", ".join(m["title"] for m in ms))
    _frame(svg)
    svg.add(header(svg, "LOCKED LEVELS", "PLANNED · NOT STARTED YET"))
    svg.defs.append('<pattern id="hz" width="12" height="12" patternUnits="userSpaceOnUse" '
                    'patternTransform="rotate(45)"><rect width="6" height="12" fill="#ffc21a" '
                    'opacity=".07"/></pattern>')
    n = max(1, len(ms))
    gap = 12
    bw = (W - 44 - gap * (n - 1)) / n
    for i, m in enumerate(ms):
        x = 22 + i * (bw + gap)
        shape = _tile_shape(x, 52, bw, 56, 10)
        svg.add(f'<path d="{shape}" fill="{C["panel2"]}" stroke="#f1eefa" stroke-opacity=".16"/>'
                f'<path d="{shape}" fill="url(#hz)"/>'
                + art.icon("lock", x + 14, 63, 16, C["ink3"])
                + svg.text(m["title"], x + 38, 77, "title", 16, C["ink2"], track=0.03, max_width=bw - 50)
                + svg.text((m.get("unlock") or "planned").upper(), x + 14, 97, "uim", 9.5, C["ink3"],
                           track=0.06, max_width=bw - 28))
    _border(svg)
    return svg


# ------------------------------------------------------------- codeforces

CF_BANDS = [(0, 1200, "#808080", "NEWBIE"), (1200, 1400, "#008000", "PUPIL"),
            (1400, 1600, "#03a89e", "SPECIALIST"), (1600, 1900, "#3b5bff", "EXPERT"),
            (1900, 2100, "#aa00aa", "CANDIDATE MASTER"), (2100, 2400, "#ff8c00", "MASTER"),
            (2400, 9999, "#ff2a2a", "GRANDMASTER")]


def _cf_colour(rating):
    for lo, hi, c, _ in CF_BANDS:
        if rating is not None and lo <= rating < hi:
            return c
    return "#808080"


def codeforces(cf, now):
    H = 240
    rating = cf.get("rating")
    svg = Svg(W, H, "Codeforces rating",
              f"Codeforces {cf['handle']}: rating {rating}, max {cf.get('max_rating')}, "
              f"{cf['contests']} rated contests, {cf['solved']} problems solved.")
    _frame(svg)
    svg.add(header(svg, "SNIPER RANGE", f"CODEFORCES · @{cf['handle'].upper()} · LIVE FROM THE CF API"))
    col = _cf_colour(rating)
    svg.add(f'<rect x="22" y="56" width="10" height="10" rx="2" fill="{col}"/>',
            svg.text((cf.get("rank") or "unrated").upper(), 40, 65.5, "uib", 11.5, C["ink2"], track=0.12),
            svg.text(fmt_int(rating) if rating else "—", 22, 118, "uib", 48, C["ink"]),
            svg.text(f"MAX {fmt_int(cf['max_rating']) if cf.get('max_rating') else '—'} · "
                     f"{(cf.get('max_rank') or '').upper()}", 22, 140, "uim", 10.5, C["ink3"],
                     track=0.08, max_width=250))
    for i, (label, value, ic) in enumerate((("RATED CONTESTS", cf["contests"], "target"),
                                            ("PROBLEMS SOLVED", cf["solved"], "check"))):
        x = 22 + i * 146
        svg.add(f'<path d="{_tile_shape(x, 156, 136, 64)}" fill="{C["panel2"]}" stroke="#f1eefa" '
                'stroke-opacity=".16"/>' + art.icon(ic, x + 10, 166, 13, C["ammo"])
                + svg.text(label, x + 28, 177, "uim", 9, C["ink3"], track=0.06, max_width=102)
                + svg.text(fmt_int(value), x + 10, 208, "uib", 22, C["ink"]))
    hist = cf.get("history") or []
    cx0, cx1, cy0, cy1 = 362, W - 48, 52, H - 36
    if len(hist) >= 2:
        rs = [r for _, r in hist]
        lo = max(0, (min(rs) // 100) * 100 - 100)
        hi = (max(rs) // 100) * 100 + 200
        ts = [t for t, _ in hist]
        t0, t1 = ts[0], ts[-1] if ts[-1] > ts[0] else ts[0] + 1

        def X(t):
            return cx0 + (t - t0) / (t1 - t0) * (cx1 - cx0)

        def Y(r):
            return cy1 - (r - lo) / (hi - lo) * (cy1 - cy0)
        for blo, bhi, c, _ in CF_BANDS:
            a, b = max(blo, lo), min(bhi, hi)
            if a < b:
                svg.add(f'<rect x="{cx0}" y="{Y(b):.1f}" width="{cx1 - cx0}" height="{Y(a) - Y(b):.1f}" '
                        f'fill="{c}" opacity=".16"/>')
                if blo > lo:
                    svg.add(f'<rect x="{cx0}" y="{Y(blo):.1f}" width="{cx1 - cx0}" height="1" '
                            f'fill="{C["line2"]}"/>'
                            + svg.text(str(blo), cx0 - 8, Y(blo) + 3.5, "uim", 9, C["ink3"], anchor="end"))
        pts = [(X(t), Y(r)) for t, r in hist]
        line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        area = line + f" L{pts[-1][0]:.1f},{cy1} L{pts[0][0]:.1f},{cy1} Z"
        svg.add(f'<path d="{area}" fill="{C["ink"]}" opacity=".07"/>',
                f'<path d="{line}" fill="none" stroke="{C["ink"]}" stroke-width="2" '
                'stroke-linejoin="round" stroke-linecap="round" pathLength="100" class="draw"/>')
        ex, ey = pts[-1]
        svg.add(f'<g class="scope"><circle cx="{ex:.1f}" cy="{ey:.1f}" r="15" fill="none" '
                f'stroke="{C["alert"]}" stroke-width="1.6"/>'
                f'<path d="M{ex - 21:.1f},{ey:.1f} h10 M{ex + 11:.1f},{ey:.1f} h10 '
                f'M{ex:.1f},{ey - 21:.1f} v10 M{ex:.1f},{ey + 11:.1f} v10" stroke="{C["alert"]}" '
                'stroke-width="1.6"/></g>'
                f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4.5" fill="{col}" stroke="{C["panel"]}" '
                'stroke-width="2"/>')
        d0 = dt.datetime.fromtimestamp(t0, dt.timezone.utc).strftime("%b %Y").upper()
        d1 = dt.datetime.fromtimestamp(t1, dt.timezone.utc).strftime("%b %Y").upper()
        svg.add(svg.text(d0, cx0, H - 18, "uim", 9.5, C["ink3"], track=0.08),
                svg.text(d1, cx1, H - 18, "uim", 9.5, C["ink3"], anchor="end", track=0.08))
    else:
        svg.add(svg.text("RATING GRAPH APPEARS AFTER TWO RATED CONTESTS", (cx0 + cx1) / 2,
                         (cy0 + cy1) / 2, "uib", 11, C["ink3"], anchor="middle", track=0.08))
    svg.style(".draw{stroke-dasharray:100;animation:draw 1.8s ease-out .2s both}"
              "@keyframes draw{from{stroke-dashoffset:100}to{stroke-dashoffset:0}}"
              ".scope{transform-box:fill-box;transform-origin:center;animation:scope 2.4s ease-in-out infinite}"
              "@keyframes scope{0%,100%{transform:scale(1) rotate(0)}50%{transform:scale(.82) rotate(45deg)}}")
    _border(svg)
    return svg


# ------------------------------------------------------------ intel, footer

def intel_header():
    svg = Svg(W, 52, "Intel reports", "Latest posts on Medium")
    _frame(svg, cut=12)
    svg.add(f'<rect x="20" y="14" width="24" height="24" rx="5" fill="#000"/>',
            art.brand("medium", 24, 18, 16, "#fff"),
            fire_text(svg, "INTEL REPORTS", 56, 34, 19),
            svg.text("LATEST WRITING ON MEDIUM · AUTO-UPDATED", W - 26, 32, "uim", 10.5, C["ink3"],
                     anchor="end", track=0.08))
    _border(svg, cut=12)
    return svg


def footer(snap, cfg, now):
    H = 96
    t, tz = local_time(now, cfg)
    svg = Svg(W, H, "Footer", "Refreshed daily by GitHub Actions.")
    clip = _frame(svg, fill="#2e3160")
    svg.defs.append('<linearGradient id="fsky" x1="0" y1="0" x2="0" y2="1">'
                    '<stop offset="0" stop-color="#58498e"/><stop offset="1" stop-color="#2f3162"/>'
                    '</linearGradient>')
    svg.add(f'<g clip-path="url(#{clip})"><rect width="{W}" height="{H}" fill="url(#fsky)"/>'
            + art.bushes(W, 92, seed=12, colour="#07080c") + "</g>")
    svg.add(f'<g transform="translate(62 44)"><g class="bob"><g transform="scale(.55)">'
            + art.soldier(svg) + "</g></g></g>")
    svg.add(fire_text(svg, "GG! THANKS FOR SCOUTING THIS PROFILE", 112, 40, 17),
            svg.text(f"NUMBERS REFRESH DAILY VIA GITHUB ACTIONS · LAST SYNC "
                     f"{t.strftime('%d %b %Y %H:%M').upper()} {tz}", 112, 60, "uim", 10, C["ink2"],
                     track=0.06, max_width=560),
            svg.text("FAN TRIBUTE TO MINI MILITIA – DOODLE ARMY 2. EVERY PIXEL DRAWN IN CODE.", 112, 75,
                     "uim", 10, C["ink2"], track=0.06, max_width=560))
    for i, word in enumerate(("3", "2", "1", "GO")):
        extra = " go" if word == "GO" else ""
        # negative delays: every digit starts mid-cycle, so none shows early
        svg.add(f'<g class="cd{extra}" style="animation-delay:{(i - 4) if i else 0}s">'
                + svg.text(word, W - 74, 58, "pixel", 26, C["alert"], anchor="middle",
                           stroke="#0b0a10", sw=1.5) + "</g>")
    svg.add(svg.text("RESPAWN", W - 74, 76, "pixel", 8, C["ink2"], anchor="middle", track=0.1))
    svg.style(".bob{animation:bob 2.8s ease-in-out infinite}"
              "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}"
              ".flame{animation:fl .14s ease-in-out infinite alternate}"
              "@keyframes fl{from{transform:scale(1,1)}to{transform:scale(.84,.7)}}"
              ".cd{opacity:0;animation:cd 4s steps(1) infinite}.go{opacity:1}"
              "@keyframes cd{0%{opacity:1}25%,100%{opacity:0}}")
    _border(svg)
    return svg
