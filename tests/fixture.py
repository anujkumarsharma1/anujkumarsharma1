"""Synthetic snapshot for tests and offline previews.

These numbers are made up. They exercise the renderers; they are never
published. The real profile is rendered only from data/snapshot.json, which
the workflow fills from the live APIs.
"""
import datetime as dt
import random

NOW = dt.datetime(2026, 9, 28, 3, 17, tzinfo=dt.timezone.utc)


def snapshot(seed=4, busy=1.0, now=NOW):
    rnd = random.Random(seed)
    today = now.date()
    # last 53 weeks, Sunday-first like GitHub's calendar
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks, daily = [], {}
    day = start
    while day <= today:
        week = []
        for _ in range(7):
            if day > today:
                break
            active = rnd.random() < 0.55 * busy
            n = rnd.choice((1, 1, 2, 3, 4, 6, 9, 13)) if active else 0
            daily[day.isoformat()] = n
            week.append({"date": day.isoformat(), "count": n, "level": 0})
            day += dt.timedelta(days=1)
        weeks.append(week)
    counts = sorted(n for n in daily.values() if n)
    q = [counts[int(len(counts) * f)] for f in (0.25, 0.5, 0.75)] if counts else [1, 2, 3]
    for w in weeks:
        for d in w:
            n = d["count"]
            d["level"] = 0 if n == 0 else 1 if n <= q[0] else 2 if n <= q[1] else 3 if n <= q[2] else 4
    iso = lambda days: (now - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    repos = [
        {"name": "kavach", "description": "", "url": "https://github.com/anujkumarsharma1/kavach",
         "stars": 3, "forks": 0, "pushed_at": iso(12), "archived": False, "language": "Python",
         "languages": {"Python": 61000}},
        {"name": "neetcode-submissions", "description": "", "url": "", "stars": 0, "forks": 0,
         "pushed_at": iso(3), "archived": False, "language": "C++",
         "languages": {"C++": 88000, "Python": 9000}},
        {"name": "spotifyclone", "description": "", "url": "", "stars": 1, "forks": 0,
         "pushed_at": iso(300), "archived": False, "language": "JavaScript",
         "languages": {"JavaScript": 21000, "HTML": 18000, "CSS": 16000}},
        {"name": "league-server", "description": "", "url": "", "stars": 0, "forks": 0,
         "pushed_at": iso(1), "archived": False, "language": "Go", "languages": {"Go": 900}},
        {"name": "raft-kv", "description": "", "url": "", "stars": 0, "forks": 0,
         "pushed_at": iso(1), "archived": False, "language": "Go", "languages": {"Go": 700}},
    ]
    return {
        "_note": "SYNTHETIC TEST DATA - not real statistics",
        "synced_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "github": {
            "login": "anujkumarsharma1", "name": "Anuj Kumar Sharma",
            "bio": "", "location": "Pune India", "created_at": "2024-09-12T13:55:50Z",
            "avatar": None, "followers": 12, "pull_requests": 17, "issues": 5,
            "repo_count": 23, "repos": repos,
            "commits_all_time": 612, "contributions_all_time": 845,
            "contributions_last_year": sum(daily.values()), "calendar": weeks, "daily": daily,
            "events": [
                {"kind": "push", "repo": "kavach", "n": 3, "when": iso(0.2)},
                {"kind": "create", "repo": "raft-kv", "when": iso(1)},
                {"kind": "merge", "repo": "zero-to-hero", "n": 4, "when": iso(2)},
            ],
        },
        "codeforces": {
            "handle": "tourist_fan", "rating": 1432, "max_rating": 1487, "rank": "specialist",
            "max_rank": "specialist", "contests": 21, "solved": 318,
            "history": [[int((now - dt.timedelta(days=400 - i * 19)).timestamp()),
                         r] for i, r in enumerate([1187, 1105, 1210, 1275, 1233, 1302, 1356,
                                                   1321, 1388, 1402, 1379, 1441, 1487, 1455,
                                                   1398, 1420, 1463, 1431, 1409, 1447, 1432])],
        },
        "medium": {"handle": "someone", "posts": [
            {"title": "Hiding malware in model weights, and catching it", "link": "https://medium.com/p/1",
             "date": "Tue, 16 Sep 2026 10:00:00 GMT"},
            {"title": "What MIT 6.5840 lab 2 taught me about Raft", "link": "https://medium.com/p/2",
             "date": "Sun, 31 Aug 2026 10:00:00 GMT"}]},
    }
