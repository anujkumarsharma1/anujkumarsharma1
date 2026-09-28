"""Fetch live numbers and derive the stats the panels show.

Every source is optional except GitHub. A source that fails keeps its last
good value from data/snapshot.json, so one flaky API never blanks the profile.
Standard library only.
"""
import base64
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "mini-militia-profile-builder (+https://github.com/anujkumarsharma1/anujkumarsharma1)"


class FetchError(RuntimeError):
    pass


def _request(url, data=None, headers=None, timeout=30, attempts=3, raw=False):
    hdrs = {"User-Agent": UA, **(headers or {})}
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                if raw:
                    return body, resp.headers.get("Content-Type", "")
                return json.loads(body.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(2 ** i)
    raise FetchError(f"{url}: {last}")


# ------------------------------------------------------------------ GitHub

USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    login name bio location createdAt avatarUrl(size: 240)
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description url stargazerCount forkCount pushedAt isArchived
        primaryLanguage { name }
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3,
          "FOURTH_QUARTILE": 4}


def _graphql(token, query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    res = _request("https://api.github.com/graphql", data=body,
                   headers={"Authorization": f"bearer {token}",
                            "Content-Type": "application/json"})
    if res.get("errors"):
        raise FetchError(f"GraphQL: {res['errors']}")
    return res["data"]


def _years_query(years, now):
    parts = []
    for y in years:
        start = f"{y}-01-01T00:00:00Z"
        end = now.strftime("%Y-%m-%dT%H:%M:%SZ") if y == now.year else f"{y}-12-31T23:59:59Z"
        parts.append(
            f'y{y}: contributionsCollection(from: "{start}", to: "{end}") {{ '
            "totalCommitContributions contributionCalendar { totalContributions "
            "weeks { contributionDays { date contributionCount } } } }")
    return "query($login: String!) { user(login: $login) { " + " ".join(parts) + " } }"


def fetch_github(login, token, now):
    if not token:
        raise FetchError("GITHUB_TOKEN is not set")
    user = _graphql(token, USER_QUERY, {"login": login})["user"]
    created = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    years = list(range(created.year, now.year + 1))
    yearly = _graphql(token, _years_query(years, now), {"login": login})["user"]

    days = {}
    commits_all = contrib_all = 0
    for y in years:
        col = yearly[f"y{y}"]
        commits_all += col["totalCommitContributions"]
        contrib_all += col["contributionCalendar"]["totalContributions"]
        for w in col["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]

    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [[{"date": d["date"], "count": d["contributionCount"],
               "level": LEVELS.get(d["contributionLevel"], 0)} for d in w["contributionDays"]]
             for w in cal["weeks"]]

    repos = []
    for n in user["repositories"]["nodes"]:
        repos.append({
            "name": n["name"], "description": n["description"] or "", "url": n["url"],
            "stars": n["stargazerCount"], "forks": n["forkCount"], "pushed_at": n["pushedAt"],
            "archived": n["isArchived"],
            "language": (n["primaryLanguage"] or {}).get("name"),
            "languages": {e["node"]["name"]: e["size"] for e in n["languages"]["edges"]},
        })

    events = _request(f"https://api.github.com/users/{login}/events/public?per_page=60",
                      headers={"Authorization": f"bearer {token}",
                               "Accept": "application/vnd.github+json"})

    avatar = None
    try:
        blob, ctype = _request(user["avatarUrl"], raw=True)
        avatar = f"data:{ctype.split(';')[0] or 'image/png'};base64," + base64.b64encode(blob).decode()
    except FetchError:
        pass

    return {
        "login": user["login"], "name": user["name"], "bio": user["bio"],
        "location": user["location"], "created_at": user["createdAt"], "avatar": avatar,
        "followers": user["followers"]["totalCount"],
        "pull_requests": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "repo_count": user["repositories"]["totalCount"],
        "repos": repos,
        "commits_all_time": commits_all,
        "contributions_all_time": contrib_all,
        "contributions_last_year": cal["totalContributions"],
        "calendar": weeks,
        "daily": days,
        "events": [_event(e) for e in events if _event(e)][:12],
    }


def _event(e):
    """Reduce a GitHub event to a kill-feed line, or None to skip it."""
    t, p = e.get("type"), e.get("payload") or {}
    repo = (e.get("repo") or {}).get("name", "").split("/")[-1]
    when = e.get("created_at")
    if t == "PushEvent":
        n = p.get("size") or p.get("distinct_size")
        return {"kind": "push", "repo": repo, "n": n, "when": when}
    if t == "CreateEvent" and p.get("ref_type") == "repository":
        return {"kind": "create", "repo": repo, "when": when}
    if t == "PullRequestEvent" and p.get("action") in ("opened", "closed"):
        merged = bool((p.get("pull_request") or {}).get("merged"))
        if p.get("action") == "closed" and not merged:
            return None
        return {"kind": "merge" if merged else "pr", "repo": repo,
                "n": (p.get("pull_request") or {}).get("number"), "when": when}
    if t == "ReleaseEvent":
        return {"kind": "release", "repo": repo, "when": when}
    if t == "IssuesEvent" and p.get("action") == "opened":
        return {"kind": "issue", "repo": repo, "when": when}
    return None


# -------------------------------------------------------------- Codeforces

def fetch_codeforces(handle):
    base = "https://codeforces.com/api/"
    q = urllib.parse.quote(handle)

    def call(path):
        res = _request(base + path, headers={"Accept": "application/json"})
        if res.get("status") != "OK":
            raise FetchError(f"codeforces {path}: {res.get('comment')}")
        return res["result"]

    info = call(f"user.info?handles={q}")[0]
    history = call(f"user.rating?handle={q}")
    subs = call(f"user.status?handle={q}")
    solved = {(s["problem"].get("contestId"), s["problem"].get("index"))
              for s in subs if s.get("verdict") == "OK"}
    return {
        "handle": info["handle"], "rating": info.get("rating"), "max_rating": info.get("maxRating"),
        "rank": info.get("rank", "unrated"), "max_rank": info.get("maxRank", "unrated"),
        "contests": len(history), "solved": len(solved),
        "history": [[h["ratingUpdateTimeSeconds"], h["newRating"]] for h in history],
    }


# ------------------------------------------------------------------ Medium

def fetch_medium(handle, limit=3):
    handle = handle.lstrip("@")
    body, _ = _request(f"https://medium.com/feed/@{urllib.parse.quote(handle)}", raw=True,
                       headers={"Accept": "application/rss+xml"})
    root = ET.fromstring(body)
    posts = []
    for item in root.iter("item"):
        link = (item.findtext("link") or "").split("?")[0]
        posts.append({"title": (item.findtext("title") or "").strip(), "link": link,
                      "date": item.findtext("pubDate") or ""})
    return {"handle": handle, "posts": posts[:limit]}


# ----------------------------------------------------------------- derived

def streaks(daily, today):
    """(current, longest) streaks of consecutive days with contributions.

    The current streak survives an empty "today" (the day is not over yet).
    """
    if not daily:
        return 0, 0
    active = {d for d, n in daily.items() if n > 0}
    longest = run = 0
    prev = None
    for d in sorted(active):
        day = dt.date.fromisoformat(d)
        run = run + 1 if prev is not None and (day - prev).days == 1 else 1
        longest = max(longest, run)
        prev = day
    cur = 0
    day = today if today.isoformat() in active else today - dt.timedelta(days=1)
    while day.isoformat() in active:
        cur += 1
        day -= dt.timedelta(days=1)
    return cur, longest


def languages(repos, ignore=(), top=5):
    """Top languages by bytes across repos, as [(name, share 0..1)]."""
    total = {}
    for r in repos:
        for name, size in r["languages"].items():
            if name in ignore:
                continue
            total[name] = total.get(name, 0) + size
    s = sum(total.values())
    if not s:
        return []
    ranked = sorted(total.items(), key=lambda kv: -kv[1])
    return [(name, size / s) for name, size in ranked[:top]]


RANKS = [(0, "RECRUIT"), (50, "PRIVATE"), (150, "CORPORAL"), (300, "SERGEANT"),
         (500, "STAFF SERGEANT"), (800, "LIEUTENANT"), (1200, "CAPTAIN"), (1800, "MAJOR"),
         (2600, "COLONEL"), (4000, "GENERAL")]


def rank(xp):
    """Rank index, name, and progress toward the next rank, from XP."""
    idx = max(i for i, (t, _) in enumerate(RANKS) if xp >= t)
    lo = RANKS[idx][0]
    if idx + 1 < len(RANKS):
        hi, nxt = RANKS[idx + 1]
        return idx, RANKS[idx][1], (xp - lo) / (hi - lo), hi - xp, nxt
    return idx, RANKS[idx][1], 1.0, 0, None


def ago(iso, now):
    if not iso:
        return ""
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (now - t).days
    if days < 1:
        hours = int((now - t).total_seconds() // 3600)
        return f"{max(hours, 1)}H AGO"
    if days < 60:
        return f"{days}D AGO"
    if days < 730:
        return f"{days // 30}MO AGO"
    return f"{days // 365}Y AGO"


def load_snapshot(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def refresh(cfg, snapshot, now, token=None):
    """Fetch every configured source; keep the old value when a source fails."""
    warnings = []
    snap = dict(snapshot)
    try:
        snap["github"] = fetch_github(cfg["login"], token or os.environ.get("GITHUB_TOKEN"), now)
    except FetchError as exc:
        warnings.append(f"github: {exc}")
        if "github" not in snap:
            raise
    for key, fn, handle in (("codeforces", fetch_codeforces, cfg.get("codeforces_handle")),
                            ("medium", fetch_medium, cfg.get("medium_handle"))):
        if not handle:
            snap.pop(key, None)
            continue
        try:
            snap[key] = fn(handle)
        except (FetchError, ET.ParseError, KeyError, IndexError) as exc:
            warnings.append(f"{key}: {exc}")
    snap["synced_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return snap, warnings
