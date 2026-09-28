"""Hand-built SVG art: the doodle soldier, weapon silhouettes, icons, insignia.

Everything here is original vector art drawn in code, in the spirit of
Mini Militia's doodle style. No game assets are used.
"""
import math

from .svgkit import C

OUT = C["out"]

# Soldier geometry (local units, facing right, origin at the torso centre).
PIVOT = (6.0, -12.0)  # shoulder joint the gun arm rotates around
MUZZLE = (54.0, 0.0)  # muzzle tip relative to PIVOT when the arm angle is 0
SKIN, SKIN_SH = "#e2b38a", "#c68d62"
HELMET, HELMET_SH, HELMET_HI = "#5a6a3a", "#44512b", "#75884c"
BEARD = "#4a2f1f"
SHIRT, SHIRT_SH = "#5c6c3b", "#45522c"
VEST = "#3b4427"
STRAP, SHELL = "#3a2a1c", "#e0b040"
BOOT, GLOVE = "#1f1f22", "#3b3b40"
GUN, GUN_HI = "#1e2226", "#4a525a"
CHROME, CHROME_SH = "#d6dade", "#8e959c"


def _o(w=2.6):
    return f'stroke="{OUT}" stroke-width="{w}" stroke-linejoin="round"'


def jet_flame(cls="flame", scale=1.0):
    """Starburst jet flame pointing down from a boot sole (origin at the sole)."""
    def burst(r_out, r_in, n, colour, skew=0.0):
        pts = []
        for i in range(n * 2 + 1):
            a = math.pi * (0.08 + 0.84 * i / (n * 2))  # fan out downward
            r = r_out if i % 2 == 0 else r_in
            pts.append(f"{math.cos(a) * r * 0.9:.1f},{math.sin(a) * r + skew:.1f}")
        return f'<polygon points="0,-1 {" ".join(pts)}" fill="{colour}"/>'
    body = (burst(19, 8, 6, "#ff3d12") + burst(14, 6, 6, "#ff9a1a", 1)
            + burst(8, 4, 5, "#fff1a8", 1) + '<circle cy="3" r="2.6" fill="#ffffff"/>')
    return (f'<g transform="scale({scale})"><g class="{cls}">{body}</g></g>')


def _face(svg, cx, cy, r, look=1.0, front=False):
    """Big doodle head: helmet, angry brows, beard, gritted teeth.

    look shifts the features right (3/4 view facing right); front=True centres them.
    """
    ex = 0 if front else r * 0.28 * look
    p = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SKIN}" {_o()}/>']
    if not front:
        p.append(f'<ellipse cx="{cx - r * 0.72:.1f}" cy="{cy + 2}" rx="3.6" ry="4.6" fill="{SKIN_SH}" {_o(1.8)}/>')
    # beard wraps the jaw
    bx0, bx1 = cx - r * 0.95 + ex * 0.3, cx + r * 0.95 + ex * 0.3
    p.append(f'<path d="M{bx0:.1f},{cy + 1:.1f} Q{bx0 + 1:.1f},{cy + r * 0.95:.1f} {cx + ex * 0.4:.1f},{cy + r * 1.02:.1f} '
             f'Q{bx1 - 1:.1f},{cy + r * 0.95:.1f} {bx1:.1f},{cy + 1:.1f} '
             f'Q{cx + ex * 0.4 + r * 0.45:.1f},{cy + r * 0.3:.1f} {cx + ex * 0.4:.1f},{cy + r * 0.36:.1f} '
             f'Q{cx + ex * 0.4 - r * 0.45:.1f},{cy + r * 0.3:.1f} {bx0:.1f},{cy + 1:.1f} Z" fill="{BEARD}" {_o(2.2)}/>')
    # gritted teeth
    tw, th = r * 0.62, r * 0.3
    tx, ty = cx + ex * 0.45 - tw / 2, cy + r * 0.42
    p.append(f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{tw:.1f}" height="{th:.1f}" rx="1.6" fill="#fff" {_o(1.8)}/>'
             f'<path d="M{tx + 1:.1f},{ty + th / 2:.1f} h{tw - 2:.1f} M{tx + tw * .33:.1f},{ty + 1:.1f} v{th - 2:.1f} '
             f'M{tx + tw * .66:.1f},{ty + 1:.1f} v{th - 2:.1f}" stroke="{OUT}" stroke-width="1.3"/>')
    # eyes and brows
    for side in (-1, 1):
        k = 1.0 if front else (1.0 if side > 0 else 0.82)
        exx = cx + ex + side * r * 0.36 * (1 if front else (1 if side > 0 else 0.9))
        ey = cy - r * 0.12
        p.append(f'<ellipse cx="{exx:.1f}" cy="{ey:.1f}" rx="{3.4 * k:.1f}" ry="{2.9 * k:.1f}" fill="#fff" {_o(1.5)}/>'
                 f'<circle cx="{exx + (0 if front else 0.8):.1f}" cy="{ey + 0.3:.1f}" r="{1.55 * k:.1f}" fill="{OUT}"/>')
        inner = exx - side * 4.6 * k
        outer = exx + side * 4.8 * k
        p.append(f'<path d="M{inner:.1f},{ey - 3.2:.1f} L{outer:.1f},{ey - 7.4:.1f} L{outer:.1f},{ey - 4.9:.1f} '
                 f'L{inner:.1f},{ey - 1.2:.1f} Z" fill="{OUT}"/>')
    # helmet
    hl, hr = cx - r * 1.05, cx + r * 1.08
    top = cy - r * 1.28
    rim = cy - r * 0.48
    p.append(f'<path d="M{hl:.1f},{rim:.1f} C{hl:.1f},{top:.1f} {hr:.1f},{top:.1f} {hr:.1f},{rim:.1f} '
             f'L{hr + 2:.1f},{rim + 3:.1f} Q{cx:.1f},{rim + 5.5:.1f} {hl - 2:.1f},{rim + 3:.1f} Z" '
             f'fill="{HELMET}" {_o()}/>'
             f'<path d="M{hl + .5:.1f},{rim:.1f} Q{cx:.1f},{rim + 3:.1f} {hr - .5:.1f},{rim:.1f} L{hr + 1.5:.1f},{rim + 2.8:.1f} '
             f'Q{cx:.1f},{rim + 5.3:.1f} {hl - 1.5:.1f},{rim + 2.8:.1f} Z" fill="{HELMET_SH}"/>'
             f'<path d="M{cx - r * .55:.1f},{top + r * .42:.1f} Q{cx:.1f},{top + r * .12:.1f} {cx + r * .5:.1f},{top + r * .38:.1f}" '
             f'stroke="{HELMET_HI}" stroke-width="3" fill="none" stroke-linecap="round"/>')
    return "".join(p)


def _bandolier(x0, y0, x1, y1, n=5):
    p = [f'<path d="M{x0},{y0} L{x1},{y1}" stroke="{OUT}" stroke-width="7.5" stroke-linecap="round"/>'
         f'<path d="M{x0},{y0} L{x1},{y1}" stroke="{STRAP}" stroke-width="5" stroke-linecap="round"/>']
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    for i in range(n):
        t = (i + 0.7) / (n + 0.4)
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        p.append(f'<rect x="{x - 1.6:.1f}" y="{y - 4.2:.1f}" width="3.2" height="6" rx="1.2" fill="{SHELL}" '
                 f'stroke="{OUT}" stroke-width="1" transform="rotate({ang - 90:.0f} {x:.1f} {y:.1f})"/>')
    return "".join(p)


def _rifle():
    """Black assault rifle, barrel along +x, grip at the origin."""
    return (f'<path d="M-9,-4 h13 v9 h-10 l-3,-2 z" fill="#2a2f35" {_o(1.8)}/>'
            f'<rect x="3" y="-5" width="31" height="9.5" rx="2" fill="{GUN}" {_o(1.8)}/>'
            f'<rect x="33" y="-2" width="19" height="4" rx="1" fill="{GUN}" {_o(1.6)}/>'
            f'<rect x="50" y="-2.9" width="5" height="5.8" rx="1" fill="{GUN_HI}" {_o(1.2)}/>'
            f'<path d="M18,4 l6.5,0 l3.8,11 l-6.3,1.2 z" fill="#2a2f35" {_o(1.6)}/>'
            f'<rect x="11" y="-9" width="12" height="4" rx="1" fill="{GUN_HI}" {_o(1.4)}/>'
            f'<path d="M6,-1.8 h26" stroke="{GUN_HI}" stroke-width="1.4"/>')


def _deagle():
    """Chrome Desert Eagle, barrel along +x, grip at the origin; muzzle at (40,-1.5)."""
    return (f'<path d="M4,3 h9 l-2,13 h-9 z" fill="{CHROME_SH}" {_o(1.8)}/>'
            f'<rect x="1" y="-6" width="39" height="9" rx="2" fill="{CHROME}" {_o(1.9)}/>'
            f'<path d="M4,-3.5 h32" stroke="#ffffff" stroke-width="1.4" opacity=".8"/>'
            f'<path d="M8,1 h26" stroke="{CHROME_SH}" stroke-width="1.2"/>'
            f'<path d="M13,3 q5,0 5,5 h-3 q0,-2.5 -2,-2.5 z" fill="{CHROME_SH}" {_o(1.2)}/>')


def soldier(svg=None, arm_cls="arm", flame_cls="flame", flash_cls=None, **_):
    """Side-scrolling player, facing right, in the doodle style of the game."""
    camo = svg.paint("camo") if svg else "#6b7b43"
    p = []
    # boot flames (drawn first, below the boots)
    p.append(f'<g transform="translate(-11 41)">{jet_flame(flame_cls, 0.8)}</g>'
             f'<g transform="translate(6 43)">{jet_flame(flame_cls, 0.85)}</g>')
    # back leg + boot
    p.append(f'<g transform="rotate(10 -8 10)"><rect x="-14" y="8" width="11" height="27" rx="5" '
             f'fill="{camo}" {_o()}/><path d="M-17,32 h13 q4,0 4,4 v4 h-18 q-2,0 -2,-3 z" fill="{BOOT}" {_o(2.2)}/></g>')
    # front leg + boot
    p.append(f'<g transform="rotate(-5 3 10)"><rect x="-2" y="8" width="11.5" height="28" rx="5" '
             f'fill="{camo}" {_o()}/><path d="M-4,33 h14 q4.5,0 4.5,4.5 v3.5 h-19 q-2,0 -2,-3 z" fill="{BOOT}" {_o(2.2)}/></g>')
    # torso
    p.append(f'<path d="M-14,-13 q0,-9 9,-9 h11 q9,0 10,9 l1,21 q0,5 -5,5 h-21 q-5,0 -5,-5 z" fill="{SHIRT}" {_o()}/>'
             f'<path d="M-12,-2 q10,4 25,0 v9 q-12,4 -25,0 z" fill="{SHIRT_SH}"/>'
             f'<rect x="-14" y="8" width="30" height="5" fill="#2b2418" {_o(1.6)}/>'
             f'<rect x="-1" y="8.4" width="5" height="4.2" rx="1" fill="#c9a24a"/>')
    p.append(_bandolier(-10, -19, 12, 7))
    # head
    p.append(_face(svg, 5, -38, 19))
    # arm with rifle, rotating around the shoulder
    arm = [f'<g transform="translate(15 5)">{_rifle()}</g>',
           f'<path d="M0,0 L12,4.5" stroke="{OUT}" stroke-width="11.5" stroke-linecap="round"/>'
           f'<path d="M0,0 L12,4.5" stroke="{SHIRT}" stroke-width="7.5" stroke-linecap="round"/>',
           f'<circle cx="15" cy="5.5" r="4.6" fill="{GLOVE}" {_o(1.8)}/>']
    if flash_cls:
        arm.append(f'<g transform="translate({MUZZLE[0] + 15 + 3} {5})"><g class="{flash_cls}">'
                   '<path d="M0,0 L10,-6 L8,-1.5 L18,0 L8,1.5 L10,6 Z" fill="#ffe066"/>'
                   '<circle r="3.2" fill="#fff6c8"/></g></g>')
    p.append(f'<g transform="translate({PIVOT[0]} {PIVOT[1]})"><g class="{arm_cls}">' + "".join(arm) + "</g></g>")
    return "".join(p)


# Front-facing hero pose: dual Desert Eagles, arms raised, boots firing.
SHOULDERS = ((-16.0, -15.0), (16.0, -15.0))
GUN_TIP = (58.0, -1.5)  # muzzle relative to a shoulder when the arm points along +x


def soldier_front(svg, arm_cls=("armL", "armR"), flame_cls="flame", flash_cls="mf"):
    camo = svg.paint("camo")
    p = []
    for x in (-8.5, 8.5):
        p.append(f'<g transform="translate({x} 44)">{jet_flame(flame_cls, 1.05)}</g>')
    for x in (-15, 3):
        p.append(f'<rect x="{x}" y="9" width="12" height="27" rx="5" fill="{camo}" {_o()}/>'
                 f'<path d="M{x - 2},{33} h{16} q3,0 3,4 v4 h-{19} q-2,0 -2,-3 z" fill="{BOOT}" {_o(2.2)}/>')
    p.append(f'<path d="M-18,-12 q0,-10 10,-10 h16 q10,0 10,10 l1,20 q0,5 -5,5 h-28 q-5,0 -5,-5 z" '
             f'fill="{SHIRT}" {_o()}/>'
             f'<path d="M-12,-19 h24 l2,20 q-14,5 -28,0 z" fill="{VEST}" opacity=".9"/>'
             f'<rect x="-18" y="8" width="36" height="5" fill="#2b2418" {_o(1.6)}/>'
             f'<rect x="-3" y="8.4" width="6" height="4.2" rx="1" fill="#c9a24a"/>')
    p.append(_bandolier(-13, -19, 13, 7, 6))
    # arms: each drawn pointing along +x from its shoulder; the left one mirrored
    for side, (sx, sy), cls in ((-1, SHOULDERS[0], arm_cls[0]), (1, SHOULDERS[1], arm_cls[1])):
        arm = (f'<g transform="translate(18 1)">{_deagle()}</g>'
               f'<path d="M0,0 L17,1" stroke="{OUT}" stroke-width="12" stroke-linecap="round"/>'
               f'<path d="M0,0 L17,1" stroke="{SHIRT}" stroke-width="8" stroke-linecap="round"/>'
               f'<circle cx="19" cy="2" r="5" fill="{GLOVE}" {_o(1.8)}/>')
        if flash_cls:
            arm += (f'<g transform="translate({GUN_TIP[0] + 2} {GUN_TIP[1]})"><g class="{flash_cls}">'
                    '<path d="M0,0 L11,-7 L9,-2 L20,0 L9,2 L11,7 Z" fill="#ffe066"/>'
                    '<circle r="3.6" fill="#fff6c8"/></g></g>')
        mirror = ' transform="scale(-1 1)"' if side < 0 else ""
        p.append(f'<g transform="translate({sx} {sy})"><g{mirror}><g class="{cls}">{arm}</g></g></g>')
    p.append(_face(svg, 0, -43, 22, front=True))
    return "".join(p)


def front_muzzle(px, py, scale, side, angle_deg):
    """World muzzle position of the hero's left (side=-1) or right (side=1) gun."""
    sx, sy = SHOULDERS[0] if side < 0 else SHOULDERS[1]
    a = math.radians(angle_deg)
    lx = math.cos(a) * GUN_TIP[0] - math.sin(a) * GUN_TIP[1]
    ly = math.sin(a) * GUN_TIP[0] + math.cos(a) * GUN_TIP[1]
    return px + scale * (sx + side * lx), py + scale * (sy + ly)


def front_aim(px, py, scale, side, tx, ty):
    """Arm angle (local, before mirroring) that points one hero gun at (tx, ty)."""
    sx, sy = SHOULDERS[0] if side < 0 else SHOULDERS[1]
    dx = ((tx - px) / scale - sx) * side
    dy = (ty - py) / scale - sy
    return math.degrees(math.atan2(dy, dx) - math.atan2(GUN_TIP[1], GUN_TIP[0]))


def muzzle_world(px, py, scale, facing, angle_deg):
    """World position of the muzzle for a side soldier drawn at (px, py)."""
    a = math.radians(angle_deg)
    mx, my = MUZZLE[0] + 15, 5.0  # rifle is mounted 15 units along the arm
    lx = PIVOT[0] + math.cos(a) * mx - math.sin(a) * my
    ly = PIVOT[1] + math.sin(a) * mx + math.cos(a) * my
    return px + facing * scale * lx, py + scale * ly


def aim_angle(px, py, scale, facing, tx, ty):
    """Arm angle (degrees, local frame) that points the barrel at (tx, ty)."""
    lx = (tx - px) / (facing * scale) - PIVOT[0]
    ly = (ty - py) / scale - PIVOT[1]
    return math.degrees(math.atan2(ly, lx) - math.atan2(5.0, MUZZLE[0] + 15))


def streak(svg, x0, y0, x1, y1, w0=5.0, w1=1.2, cls="shot", style=""):
    """Tapered tracer like the game's splash: red at the gun, yellow at the tip."""
    gid = svg.uid("st")
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1
    nx, ny = -dy / n, dx / n
    svg.defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x0:.1f}" y1="{y0:.1f}" '
                    f'x2="{x1:.1f}" y2="{y1:.1f}"><stop offset="0" stop-color="#ff2a1a"/>'
                    '<stop offset=".35" stop-color="#ff8a1a"/><stop offset="1" stop-color="#fff36a"/>'
                    '</linearGradient>')
    pts = (f"{x0 + nx * w0 / 2:.1f},{y0 + ny * w0 / 2:.1f} {x1 + nx * w1 / 2:.1f},{y1 + ny * w1 / 2:.1f} "
           f"{x1 - nx * w1 / 2:.1f},{y1 - ny * w1 / 2:.1f} {x0 - nx * w0 / 2:.1f},{y0 - ny * w0 / 2:.1f}")
    return f'<polygon points="{pts}" fill="url(#{gid})" class="{cls}" style="{style}"/>'


# ---------------------------------------------------------------- jungle

LEAF_DARK, LEAF, LEAF_LIGHT, RIM = "#1b3318", "#294a23", "#3a6331", "#ff7a1a"


def leaf(x, y, length, angle, width=0.34, shade=LEAF, rim=True, veins=4):
    """A broad jungle leaf with an orange rim light, pointing along `angle`."""
    L, Wd = length, length * width
    body = (f"M0,0 C{L * .2:.1f},{-Wd:.1f} {L * .72:.1f},{-Wd * .9:.1f} {L:.1f},0 "
            f"C{L * .72:.1f},{Wd * .9:.1f} {L * .2:.1f},{Wd:.1f} 0,0 Z")
    p = []
    if rim:
        p.append(f'<path d="{body}" fill="{RIM}" transform="translate(1.6 1.6)"/>')
    p.append(f'<path d="{body}" fill="{shade}" stroke="#08120a" stroke-width="2"/>')
    p.append(f'<path d="M0,0 Q{L * .5:.1f},{-Wd * .08:.1f} {L * .97:.1f},0" stroke="#10220f" stroke-width="1.6" fill="none"/>')
    for i in range(1, veins + 1):
        t = i / (veins + 1)
        vx = L * t
        for sgn in (-1, 1):
            p.append(f'<path d="M{vx:.1f},0 L{vx + L * .12:.1f},{sgn * Wd * .62 * (1 - abs(t - .45)):.1f}" '
                     'stroke="#10220f" stroke-width="1.1"/>')
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({angle:.1f})">' + "".join(p) + "</g>"


def frond(x, y, length, angle, curl=0.25, n=9, shade=LEAF, rim=True):
    """Palm frond: a curved rib with leaflets along both sides."""
    p = [f'<path d="M0,0 Q{length * .5:.1f},{-length * curl:.1f} {length:.1f},{length * curl * .6:.1f}" '
         'stroke="#08120a" stroke-width="3.2" fill="none"/>']
    for i in range(n):
        t = (i + 1) / (n + 1)
        bx = length * t
        by = -length * curl * 2 * t * (1 - t) + length * curl * .6 * t * t
        ln = length * (0.42 - 0.26 * t)
        for sgn in (-1, 1):
            a = sgn * (58 - 18 * t) + 12
            p.append(leaf(bx, by, ln, a, 0.18, shade, rim, veins=0))
    return f'<g transform="translate({x:.1f} {y:.1f}) rotate({angle:.1f})">' + "".join(p) + "</g>"


def bushes(width, y, seed=3, colour="#06090a"):
    """Spiky black undergrowth along the bottom edge."""
    import random as _r
    rnd = _r.Random(seed)
    pts = [f"0,{y + 40}"]
    x = 0.0
    while x < width:
        h = rnd.uniform(10, 34)
        w = rnd.uniform(8, 22)
        pts.append(f"{x:.0f},{y:.0f}")
        pts.append(f"{x + w * .5:.0f},{y - h:.0f}")
        x += w
    pts.append(f"{width},{y}")
    pts.append(f"{width},{y + 40}")
    return f'<polygon points="{" ".join(pts)}" fill="{colour}"/>'


def hud_frame(x, y, w, h, cut=14, opacity=0.75):
    """The game's HUD frame: a light double border with a cut bottom-right corner."""
    d = (f"M{x},{y} H{x + w} V{y + h - cut} L{x + w - cut},{y + h} H{x} Z")
    d2 = (f"M{x + 5},{y + 5} H{x + w - 5} V{y + h - cut - 2} L{x + w - cut - 2},{y + h - 5} H{x + 5} Z")
    return (f'<path d="{d}" fill="#0b0a14" fill-opacity=".45" stroke="#f1eefa" stroke-opacity="{opacity}" '
            'stroke-width="3"/>'
            f'<path d="{d2}" fill="none" stroke="#f1eefa" stroke-opacity="{opacity * .45:.2f}" stroke-width="1.2"/>')


def heart(x, y, s=14, colour="#f1eefa"):
    k = s / 16
    return (f'<g transform="translate({x} {y}) scale({k:.3f})"><path d="M8,14.5 C2,10 0,7.5 0,4.6 '
            f'C0,2 2,0 4.5,0 C6,0 7.3,.8 8,2 C8.7,.8 10,0 11.5,0 C14,0 16,2 16,4.6 C16,7.5 14,10 8,14.5 Z" '
            f'fill="{colour}"/></g>')


def jet_icon(x, y, s=14, colour="#f1eefa"):
    k = s / 16
    return (f'<g transform="translate({x} {y}) scale({k:.3f})"><path d="M8,0 L12,6 H9.5 V13 L8,16 L6.5,13 '
            f'V6 H4 Z" fill="{colour}"/></g>')


def head_icon(svg, x, y, s=28):
    """Small helmeted head for counters, like the game's lives display."""
    k = s / 44
    return f'<g transform="translate({x} {y}) scale({k:.3f})">' + _face(svg, 0, 0, 19, front=True) + "</g>"


def drone(x, y, s=1.0, cls="drone"):
    """A silver survival-mode style robot drone with red eyes (original drawing)."""
    return (f'<g transform="translate({x} {y}) scale({s})"><g class="{cls}">'
            f'<g transform="translate(0 16)">{jet_flame("flame", .6)}</g>'
            f'<path d="M-24,4 Q-24,-22 0,-22 Q24,-22 24,4 Q12,10 0,10 Q-12,10 -24,4 Z" fill="#d9dde2" {_o()}/>'
            f'<path d="M-20,-2 Q0,-12 20,-2" stroke="#9aa1a8" stroke-width="2" fill="none"/>'
            f'<path d="M-14,-4 L-4,-1 L-5,2 L-15,-1 Z M14,-4 L4,-1 L5,2 L15,-1 Z" fill="#ff2a1a" {_o(1.2)}/>'
            f'<path d="M-22,-8 L-34,-26 L-26,-8 Z M22,-8 L34,-26 L26,-8 Z" fill="#c4c9cf" {_o(2)}/>'
            f'<rect x="-16" y="6" width="32" height="6" rx="2" fill="#3b3f45" {_o(1.6)}/>'
            '</g></g>')


# ---------------------------------------------------------------- weapons
# Silhouettes in a 72 x 24 box, barrel pointing right.

def _r(x, y, w, h, rx=1.2, fill=None):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>'


def weapon(name, x, y, scale=1.0, fill="#cfd8cc", accent=None):
    accent = accent or C["ammo"]
    f = fill
    s = {
        "M4": [
            f'<path d="M0,8 h11 l3,-3 v10 l-3,-1 h-11 z" fill="{f}"/>',
            _r(13, 5, 26, 8, fill=f), _r(18, 1.5, 13, 3, fill=f), _r(38, 7, 24, 3, fill=f),
            _r(50, 3.5, 2.2, 4, fill=f), _r(27, 12, 5.5, 10, fill=f),
            f'<path d="M17,12 h4.5 l-2,8 h-4 z" fill="{f}"/>'],
        "AK47": [
            f'<path d="M0,10 l13,-4 v8 l-11,4 z" fill="{f}"/>', _r(13, 5, 25, 8, fill=f),
            _r(38, 7.5, 24, 2.6, fill=f), _r(38, 4.8, 14, 2.2, fill=f),
            f'<path d="M26,13 q2,6 7,9 l3.5,-2.4 q-4,-3 -5,-6.6 z" fill="{f}"/>',
            f'<path d="M17,13 h4.5 l-2,7 h-4 z" fill="{f}"/>'],
        "M93BA": [
            f'<path d="M0,7 h13 v7 h-9 l-4,2 z" fill="{f}"/>', _r(13, 6, 22, 7, fill=f),
            _r(35, 8, 37, 2.4, fill=f), _r(15, 0.5, 20, 4.6, 2, fill=f),
            _r(14, 1.2, 2, 3.2, fill=accent), f'<path d="M22,13 h4 l-1,6 h-3 z" fill="{f}"/>',
            f'<path d="M56,10 l-4,9 M56,10 l4,9" stroke="{f}" stroke-width="1.6"/>'],
        "UZI": [
            _r(14, 5, 25, 8, fill=f), _r(39, 7, 8, 3, fill=f), _r(3, 7, 12, 2.2, fill=f),
            f'<path d="M23,13 h6 l-1,11 h-6 z" fill="{f}"/>', _r(19, 2.5, 6, 2.5, fill=f)],
        "MP5": [
            f'<path d="M2,7 h11 v7 h-11 z" fill="{f}"/>', _r(13, 5, 25, 7.5, fill=f),
            _r(38, 7, 12, 2.6, fill=f),
            f'<path d="M26,12.5 q1,6 5,9 l3,-2 q-3,-3 -3.6,-7 z" fill="{f}"/>',
            f'<path d="M17,12 h4.5 l-2,7 h-4 z" fill="{f}"/>'],
        "SHOTGUN": [
            f'<path d="M0,9 l14,-3 v8 l-12,3 z" fill="{f}"/>', _r(14, 5.5, 14, 7.5, fill=f),
            _r(28, 6, 36, 2.6, fill=f), _r(30, 9.2, 26, 2.3, fill=f), _r(38, 8.2, 11, 4.6, 2, fill=f)],
        "DEAGLE": [
            _r(20, 5, 30, 7.5, 1.6, fill=f), _r(46, 6, 5, 4, fill=f),
            f'<path d="M22,12 h8 l-2,12 h-8 z" fill="{f}"/>',
            f'<path d="M30,12 q4,0 4,5 h-3 q0,-3 -2,-3 z" fill="{f}"/>'],
        "SMAW": [
            _r(4, 5, 56, 10, 3, fill=f), f'<path d="M60,4 l8,-1 v14 l-8,-1 z" fill="{f}"/>',
            _r(24, 15, 4.5, 8, fill=f), _r(28, 0.5, 9, 4.5, fill=f), _r(8, 8, 8, 4, fill=accent)],
        "SAW": [
            _r(6, 7, 26, 9, 2, fill=f), f'<path d="M14,16 h5 l-2,7 h-5 z" fill="{f}"/>',
            f'<circle cx="46" cy="11" r="10" fill="none" stroke="{f}" stroke-width="3" '
            'stroke-dasharray="3.2 2.2"/>',
            f'<circle cx="46" cy="11" r="6.5" fill="{f}"/><circle cx="46" cy="11" r="2" fill="{accent}"/>',
            _r(30, 9.5, 10, 4, fill=f)],
        "LASER": [
            f'<path d="M4,8 q4,-5 14,-5 h30 l10,5 v5 l-10,4 h-30 q-10,0 -14,-4 z" fill="{f}"/>',
            _r(18, 9, 34, 2.4, 1.2, fill="#5ff2ff"), _r(58, 9.3, 12, 1.8, 0.9, fill="#5ff2ff"),
            f'<path d="M22,16 h5 l-2,7 h-5 z" fill="{f}"/>'],
        "SHIELD": [
            f'<path d="M24,1 h24 q4,0 4,4 v12 q0,6 -16,7 q-16,-1 -16,-7 v-12 q0,-4 4,-4 z" fill="{f}"/>',
            _r(28, 6, 16, 3, 1.5, fill=C["panel"]),
            f'<circle cx="27" cy="18" r="1.4" fill="{C["panel"]}"/>'
            f'<circle cx="45" cy="18" r="1.4" fill="{C["panel"]}"/>'],
        "FRAG": [
            f'<ellipse cx="34" cy="14" rx="9" ry="10" fill="{f}"/>', _r(30, 1.5, 8, 4, fill=f),
            f'<path d="M38,4 q8,1 7,11" fill="none" stroke="{f}" stroke-width="2.4"/>',
            f'<circle cx="27" cy="5" r="3.2" fill="none" stroke="{accent}" stroke-width="1.8"/>',
            f'<path d="M26,14 h16 M34,6 v17" stroke="{C["panel"]}" stroke-width="1.4"/>'],
        "GAS": [
            _r(28, 5, 14, 19, 4, fill=f), _r(31, 1.5, 8, 4, fill=f),
            f'<circle cx="49" cy="7" r="4" fill="{f}" opacity=".55"/>'
            f'<circle cx="56" cy="4" r="3" fill="{f}" opacity=".35"/>'
            f'<circle cx="53" cy="13" r="3" fill="{f}" opacity=".4"/>',
            _r(30, 11, 10, 2.4, fill=accent)],
        "MACHETE": [
            f'<path d="M22,12 q24,-12 46,-8 q-4,8 -20,12 q-14,3 -26,0 z" fill="{f}"/>',
            _r(8, 10, 15, 5, 2, fill=f), _r(20, 8.5, 3, 8, fill=accent)],
        "M14": [
            f'<path d="M0,8 q6,-2 14,-2 l6,1 v7 l-8,1 q-8,0 -12,-3 z" fill="{f}"/>',
            _r(20, 5.5, 20, 7.5, fill=f), _r(40, 7.5, 28, 2.4, fill=f),
            _r(25, 12.5, 5.5, 8, fill=f), _r(40, 5.5, 14, 2.2, fill=f)],
    }[name]
    return (f'<g transform="translate({x} {y}) scale({scale})">' + "".join(s) + "</g>")


WEAPONS = ["M4", "AK47", "M93BA", "UZI", "MP5", "SHOTGUN", "DEAGLE", "SMAW", "SAW",
           "LASER", "SHIELD", "FRAG", "GAS", "MACHETE", "M14"]

# Language -> weapon. A few in-jokes: C++ is the sniper (competitive
# programming precision), JavaScript sprays like an Uzi, HTML is a shield.
LANGUAGE_WEAPON = {
    "C++": "M93BA", "C": "M14", "Python": "AK47", "Go": "M4", "Java": "SHOTGUN",
    "JavaScript": "UZI", "TypeScript": "MP5", "HTML": "SHIELD", "CSS": "GAS",
    "SCSS": "GAS", "Jupyter Notebook": "LASER", "Shell": "FRAG", "Rust": "SAW",
    "Kotlin": "DEAGLE", "Dart": "DEAGLE", "Dockerfile": "SMAW", "C#": "M4",
    "PHP": "MACHETE", "Ruby": "MACHETE", "Swift": "LASER", "Solidity": "SMAW",
}


def weapon_for(language, taken):
    w = LANGUAGE_WEAPON.get(language)
    if w and w not in taken:
        return w
    for cand in WEAPONS:
        if cand not in taken:
            return cand
    return "M4"


# ---------------------------------------------------------------- icons

def icon(name, x, y, s=16, colour=None):
    """Small 16x16 pictograms for stat tiles and chips."""
    c = colour or C["ammo"]
    d = {
        "bullet": f'<path d="M5,15 v-8 q0,-6 3,-7 q3,1 3,7 v8 z" fill="{c}"/>'
                  f'<rect x="4.5" y="12" width="7" height="3.5" rx=".8" fill="{C["sand"]}"/>',
        "crate": f'<rect x="1.5" y="3" width="13" height="11" rx="1.5" fill="none" stroke="{c}" '
                 f'stroke-width="1.8"/><path d="M1.5,3 l13,11 M14.5,3 l-13,11" stroke="{c}" '
                 'stroke-width="1.4"/>',
        "calendar": f'<rect x="1.5" y="3" width="13" height="11.5" rx="2" fill="none" stroke="{c}" '
                    f'stroke-width="1.8"/><path d="M1.5,7 h13 M5,1 v4 M11,1 v4" stroke="{c}" '
                    f'stroke-width="1.8"/><rect x="4" y="9.3" width="3" height="3" fill="{c}"/>',
        "flame": f'<path d="M8,1 q6,6 5,10 a5,5 0 0 1 -10,0 q0,-3 2,-5 q0,3 2,3 q-1,-4 1,-8 z" '
                 f'fill="{c}"/>',
        "medal": f'<path d="M4,1 l4,6 l4,-6" fill="none" stroke="{C["alert"]}" stroke-width="2"/>'
                 f'<circle cx="8" cy="10.5" r="4.6" fill="{c}"/>',
        "repo": f'<path d="M3,2 h9 a1.5,1.5 0 0 1 1.5,1.5 v10 h-9.5 a1.5,1.5 0 0 1 -1.5,-1.5 z" '
                f'fill="none" stroke="{c}" stroke-width="1.8"/><path d="M6,5 h4.5 M6,8 h4.5" '
                f'stroke="{c}" stroke-width="1.6"/>',
        "merge": f'<circle cx="4" cy="3.5" r="2.2" fill="none" stroke="{c}" stroke-width="1.7"/>'
                 f'<circle cx="4" cy="12.5" r="2.2" fill="none" stroke="{c}" stroke-width="1.7"/>'
                 f'<circle cx="12.5" cy="8.5" r="2.2" fill="none" stroke="{c}" stroke-width="1.7"/>'
                 f'<path d="M4,5.7 v4.6 M4,6 q0,2.5 6.3,2.5" fill="none" stroke="{c}" '
                 'stroke-width="1.7"/>',
        "star": f'<path d="M8,1 l2.1,4.6 5,.5 -3.8,3.3 1.1,4.9 -4.4,-2.6 -4.4,2.6 1.1,-4.9 '
                f'-3.8,-3.3 5,-.5 z" fill="{c}"/>',
        "target": f'<circle cx="8" cy="8" r="6" fill="none" stroke="{c}" stroke-width="1.6"/>'
                  f'<circle cx="8" cy="8" r="1.8" fill="{c}"/><path d="M8,0 v4 M8,12 v4 M0,8 h4 '
                  f'M12,8 h4" stroke="{c}" stroke-width="1.6"/>',
        "lock": f'<rect x="2.5" y="7" width="11" height="8" rx="1.8" fill="{c}"/>'
                f'<path d="M5,7 v-2.2 a3,3 0 0 1 6,0 v2.2" fill="none" stroke="{c}" '
                'stroke-width="1.9"/>',
        "check": f'<path d="M2.5,8.5 l3.8,3.8 l7.2,-8" fill="none" stroke="{c}" '
                 'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
        "gear": f'<circle cx="8" cy="8" r="3.2" fill="none" stroke="{c}" stroke-width="2"/>'
                f'<path d="M8,1 v3 M8,12 v3 M1,8 h3 M12,8 h3 M3,3 l2,2 M11,11 l2,2 M13,3 l-2,2 '
                f'M5,11 l-2,2" stroke="{c}" stroke-width="2" stroke-linecap="round"/>',
        "brief": f'<rect x="1.5" y="4.5" width="13" height="9.5" rx="1.6" fill="none" stroke="{c}" '
                 f'stroke-width="1.8"/><path d="M5.5,4.5 v-2 h5 v2 M1.5,8.5 h13" fill="none" '
                 f'stroke="{c}" stroke-width="1.6"/>',
        "radio": f'<rect x="3" y="5" width="10" height="10" rx="1.6" fill="none" stroke="{c}" '
                 f'stroke-width="1.8"/><path d="M5,5 l6,-4" stroke="{c}" stroke-width="1.6"/>'
                 f'<circle cx="8" cy="10" r="2" fill="{c}"/>',
    }[name]
    k = s / 16
    return f'<g transform="translate({x} {y}) scale({k:.3f})">{d}</g>'


def insignia(level, x, y, colour=None):
    """Rank insignia for rank index 0..9: chevrons, then bars, then stars."""
    c = colour or C["ammo"]
    parts = []
    if level == 0:
        parts.append(f'<circle cx="18" cy="18" r="9" fill="none" stroke="{c}" stroke-width="2.5"/>')
    elif level <= 4:
        n = min(level, 3)
        for i in range(n):
            yy = 8 + i * 8
            parts.append(f'<path d="M5,{yy + 8} L18,{yy} L31,{yy + 8}" fill="none" stroke="{c}" '
                         'stroke-width="4.2" stroke-linejoin="round" stroke-linecap="round"/>')
        if level == 4:
            parts.append(f'<path d="M6,31 q12,6 24,0" fill="none" stroke="{c}" stroke-width="3.6" '
                         'stroke-linecap="round"/>')
    elif level <= 6:
        for i in range(level - 4):
            parts.append(f'<rect x="{10 + i * 10}" y="6" width="6" height="24" rx="1.5" fill="{c}"/>')
    else:
        stars = level - 6
        for i in range(stars):
            cx = 18 + (i - (stars - 1) / 2) * 11
            parts.append(f'<path transform="translate({cx - 6} 12) scale(.75)" d="M8,1 l2.1,4.6 '
                         f'5,.5 -3.8,3.3 1.1,4.9 -4.4,-2.6 -4.4,2.6 1.1,-4.9 -3.8,-3.3 5,-.5 z" '
                         f'fill="{c}"/>')
    return f'<g transform="translate({x} {y})">' + "".join(parts) + "</g>"


# ---------------------------------------------------------------- brands
# Monochrome marks from Simple Icons (CC0 1.0, simpleicons.org), 24x24.
SIMPLE_ICONS = {
    "gmail": "M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z",
    "medium": "M13.54 12a6.8 6.8 0 01-6.77 6.82A6.8 6.8 0 010 12a6.8 6.8 0 016.77-6.82A6.8 6.8 0 0113.54 12zM20.96 12c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z",
    "x": "M14.234 10.162 22.977 0h-2.072l-7.591 8.824L7.251 0H.258l9.168 13.343L.258 24H2.33l8.016-9.318L16.749 24h6.993zm-2.837 3.299-.929-1.329L3.076 1.56h3.182l5.965 8.532.929 1.329 7.754 11.09h-3.182z",
}


def brand(name, x, y, s=20, colour="#fff"):
    """Brand mark drawn in an s x s box."""
    if name in SIMPLE_ICONS:
        k = s / 24
        return (f'<g transform="translate({x} {y}) scale({k:.4f})">'
                f'<path d="{SIMPLE_ICONS[name]}" fill="{colour}"/></g>')
    k = s / 24
    if name == "codeforces":
        body = ('<rect x="1" y="9" width="6" height="13" rx="1.4" fill="#fdcc2d"/>'
                '<rect x="9" y="3" width="6" height="19" rx="1.4" fill="#1f8dd6"/>'
                '<rect x="17" y="7" width="6" height="15" rx="1.4" fill="#e43b31"/>')
    elif name == "linkedin":
        body = (f'<rect x="2" y="9" width="4.5" height="13" rx=".8" fill="{colour}"/>'
                f'<circle cx="4.25" cy="4.5" r="2.6" fill="{colour}"/>'
                f'<path d="M9.5,9 h4.3 v2 q1.6,-2.4 4.6,-2.4 q4.6,0 4.6,5.6 v7.8 h-4.5 v-7 '
                f'q0,-2.7 -2.2,-2.7 q-2.3,0 -2.3,2.9 v6.8 h-4.5 z" fill="{colour}"/>')
    elif name == "topmate":
        # generic "book a call" mark: calendar with a chat bubble, not Topmate's logo
        body = (f'<rect x="2" y="4" width="16" height="15" rx="2.5" fill="none" stroke="{colour}" '
                f'stroke-width="2.2"/><path d="M2,9 h16 M6,1.5 v5 M14,1.5 v5" stroke="{colour}" '
                f'stroke-width="2.2" stroke-linecap="round"/>'
                f'<path d="M13,13 h9 a1.5,1.5 0 0 1 1.5,1.5 v5 a1.5,1.5 0 0 1 -1.5,1.5 h-4 l-3,2.5 '
                f'v-2.5 h-2 a1.5,1.5 0 0 1 -1.5,-1.5 v-5 a1.5,1.5 0 0 1 1.5,-1.5 z" fill="{colour}"/>')
    else:
        raise KeyError(name)
    return f'<g transform="translate({x} {y}) scale({k:.4f})">{body}</g>'
