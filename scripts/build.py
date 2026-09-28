"""Build the profile: fetch live numbers, render every panel, update README.md.

    python scripts/build.py               # live: fetch, render, write snapshot + README
    python scripts/build.py --offline     # re-render from data/snapshot.json, no network
    python scripts/build.py --fixture --out /tmp/preview   # synthetic data, for previews

Only the block between the mm:start / mm:end markers in README.md is generated;
anything outside it is left alone.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mm import panels  # noqa: E402
from mm.data import languages, load_snapshot, rank, refresh, streaks  # noqa: E402
from mm.svgkit import attr, fmt_int  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- mm:start -->", "<!-- mm:end -->"
GEN = "assets/generated"


def link_for(key, value):
    if key == "email":
        return f"mailto:{value}"
    return value


def render_all(snap, cfg, now):
    """Return {relative path: svg text} and the README block."""
    files = {}
    login = cfg["login"]
    g = snap["github"]

    def put(name, svg):
        files[f"{GEN}/{name}"] = svg.render()
        return f"{GEN}/{name}"

    hero = put("hero.svg", panels.hero(snap, cfg, now))
    comms = []
    order = ["linkedin", "email", "codeforces", "topmate", "x", "medium"]
    channel = 0
    for key in order:
        value = (cfg.get("links") or {}).get(key)
        if not value:
            continue
        channel += 1
        path = put(f"comms-{key}.svg", panels.comms_button(key, channel))
        label = panels.COMMS[key][0].title()
        comms.append(f'<a href="{link_for(key, value)}"><img src="{path}" height="46" '
                     f'alt="{label}"></a>')
    card = put("player-card.svg", panels.player_card(snap, cfg, now))
    loadout = put("loadout.svg", panels.loadout(snap, cfg))
    field = put("battlefield.svg", panels.battlefield(snap, cfg, now))

    missions = cfg.get("missions", [])
    featured = [m for m in missions if m["status"] == "complete"]
    regular = [m for m in missions if m["status"] in ("active", "briefed")]
    locked = [m for m in missions if m["status"] == "locked"]
    mission_html = []
    number = 0
    for m in featured:
        number += 1
        p = put(f"mission-{m['repo']}.svg", panels.mission_featured(m, snap, now, number))
        mission_html.append(f'<p align="center"><a href="https://github.com/{login}/{m["repo"]}">'
                            f'<img src="{p}" width="100%" alt="{attr(m["title"] + ": " + m.get("blurb", ""))}"></a></p>')
    pairs = []
    for m in regular:
        p = put(f"mission-{m['repo']}.svg", panels.mission_card(m, snap, now))
        pairs.append(f'<a href="https://github.com/{login}/{m["repo"]}"><img src="{p}" width="49%" '
                     f'alt="{attr(m["title"] + ": " + m.get("blurb", ""))}"></a>')
    for i in range(0, len(pairs), 2):
        mission_html.append('<p align="center">\n  ' + "\n  ".join(pairs[i:i + 2]) + "\n</p>")
    if locked:
        p = put("locked.svg", panels.locked_levels(locked))
        mission_html.append(f'<p align="center"><img src="{p}" width="100%" alt="Locked levels, '
                            f'planned next: {", ".join(m["title"] for m in locked)}"></p>')

    cf_html = ""
    cf = snap.get("codeforces")
    if cf:
        p = put("codeforces.svg", panels.codeforces(cf, now))
        cf_html = (f'<p align="center"><a href="https://codeforces.com/profile/{quote(cf["handle"])}">'
                   f'<img src="{p}" width="100%" alt="Codeforces rating {cf.get("rating")}, '
                   f'max {cf.get("max_rating")}, {cf["solved"]} problems solved"></a></p>')

    intel_html = ""
    posts = (snap.get("medium") or {}).get("posts") or []
    if posts:
        p = put("intel.svg", panels.intel_header())
        items = []
        for post in posts:
            date = post["date"][5:16] if post.get("date") else ""
            title = post["title"].replace("[", "(").replace("]", ")")
            items.append(f"- [{title}]({post['link']})" + (f" · <sub>{date}</sub>" if date else ""))
        intel_html = f'<p align="center"><img src="{p}" width="100%" alt="Intel reports"></p>\n\n' \
                     + "\n".join(items)

    foot = put("footer.svg", panels.footer(snap, cfg, now))

    # text twin of every number, for screen readers and anyone who wants the table
    tz_now, tz = panels.local_time(now, cfg)
    cur, longest = streaks(g["daily"], tz_now.date())
    idx, rname, _, _, _ = rank(g["contributions_all_time"])
    active = sum(1 for w in g["calendar"] for d in w if d["count"] > 0)
    langs = languages(g["repos"], cfg.get("ignore_languages", []))
    rows = [
        ("Commits (public, all-time)", fmt_int(g["commits_all_time"])),
        ("Contributions (last 12 months)", fmt_int(g["contributions_last_year"])),
        ("Active days (last 12 months)", fmt_int(active)),
        ("Current streak", f"{cur} days"),
        ("Best streak (all-time)", f"{longest} days"),
        ("Pull requests opened", fmt_int(g["pull_requests"])),
        ("Public repos (forks excluded)", fmt_int(g["repo_count"])),
        ("Stars from other people", fmt_int(sum(r["stars"] for r in g["repos"]))),
        ("Rank", f"{rname.title()} ({fmt_int(g['contributions_all_time'])} XP = all-time contributions)"),
        ("Top languages (share of bytes" + (", excluding " + "/".join(cfg["ignore_languages"])
                                            if cfg.get("ignore_languages") else "") + ")", ", ".join(f"{n} {s * 100:.1f}%" for n, s in langs) or "none"),
    ]
    if cf:
        rows.append(("Codeforces", f"{cf.get('rating')} ({cf.get('rank')}), max {cf.get('max_rating')}, "
                                   f"{cf['solved']} solved"))
    rows.append(("Last sync", f"{tz_now.strftime('%Y-%m-%d %H:%M')} {tz}"))
    table = "| Stat | Value |\n|---|---|\n" + "\n".join(f"| {a} | {b} |" for a, b in rows)

    total = g["contributions_last_year"]
    block = "\n\n".join(filter(None, [
        f'<p align="center"><img src="{hero}" width="100%" alt="{attr(cfg["display_name"] + ", " + cfg["headline"])}. '
        'A jetpack soldier shoots the name onto the screen."></p>',
        ('<p align="center">\n  ' + "\n  ".join(comms) + "\n</p>") if comms else "",
        f'<p align="center"><img src="{card}" width="100%" alt="Player card: '
        f'{fmt_int(g["commits_all_time"])} commits all-time, {fmt_int(total)} contributions in the '
        f'last 12 months, streak {cur} days (best {longest}), rank {rname.title()}"></p>',
        f'<p align="center"><img src="{loadout}" width="100%" alt="Armory, top languages: '
        + ", ".join(f"{n} {s * 100:.0f}%" for n, s in langs) + '"></p>',
        f'<p align="center"><img src="{field}" width="100%" alt="Contribution graph as a '
        f'battlefield: {fmt_int(total)} contributions in the last 12 months"></p>',
        "\n\n".join(mission_html),
        cf_html,
        intel_html,
        "<details>\n<summary><b>Text version</b> · every number above, as a table</summary>\n\n"
        + table + "\n\n</details>",
        f'<p align="center"><img src="{foot}" width="100%" alt="Refreshed daily by GitHub Actions"></p>',
    ]))
    return files, block


def update_readme(text, block):
    if START in text and END in text:
        head, rest = text.split(START, 1)
        _, tail = rest.split(END, 1)
        return f"{head}{START}\n{block}\n{END}{tail}"
    return f"{START}\n{block}\n{END}\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="render from data/snapshot.json only")
    ap.add_argument("--fixture", action="store_true", help="render synthetic test data (preview)")
    ap.add_argument("--out", default=str(ROOT), help="where to write assets/ and README.md")
    args = ap.parse_args(argv)

    out = Path(args.out)
    if args.fixture and out.resolve() == ROOT:
        ap.error("--fixture needs --out: synthetic data must never overwrite the real profile")
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    snap_path = ROOT / "data" / "snapshot.json"

    if args.fixture:
        sys.path.insert(0, str(ROOT / "tests"))
        from fixture import NOW, snapshot
        snap, now = snapshot(), NOW
    elif args.offline:
        snap = load_snapshot(snap_path)
        if "github" not in snap:
            ap.error("no data/snapshot.json yet: run once without --offline")
    else:
        snap, warnings = refresh(cfg, load_snapshot(snap_path), now)
        for w in warnings:
            print(f"::warning::{w}")
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        snap_path.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    files, block = render_all(snap, cfg, now)
    gen = out / GEN
    gen.mkdir(parents=True, exist_ok=True)
    for old in gen.glob("*.svg"):
        if f"{GEN}/{old.name}" not in files:
            old.unlink()
    for rel, text in files.items():
        (out / rel).write_text(text, encoding="utf-8")
    readme = out / "README.md"
    current = readme.read_text(encoding="utf-8") if readme.exists() else ""
    readme.write_text(update_readme(current, block), encoding="utf-8")
    kb = sum(len(t) for t in files.values()) // 1024
    print(f"rendered {len(files)} SVGs ({kb} KB) into {gen}")


if __name__ == "__main__":
    main()
