"""Render daily profile cards using only public, non-fork repositories."""

import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USER = "ZephyrAki"
ASSETS = Path(__file__).resolve().parents[1] / "assets"


def github(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ZephyrAki-profile"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(f"https://api.github.com{path}", headers=headers), timeout=30) as response:
        return json.load(response)


def collect(fetch=github):
    repos = []
    page = 1
    while True:
        batch = fetch(f"/users/{USER}/repos?per_page=100&page={page}")
        repos.extend(repo for repo in batch if not repo["private"] and not repo["fork"])
        if len(batch) < 100:
            break
        page += 1
    languages = Counter()
    for repo in repos:
        languages.update(fetch(f"/repos/{USER}/{repo['name']}/languages"))
    counts = [len(repos), sum(r["stargazers_count"] for r in repos), sum(r["forks_count"] for r in repos)]
    return counts, languages


def render(counts, languages, theme):
    dark = theme == "dark"
    bg, border = ("#101925", "#26364a") if dark else ("#f7faff", "#dce7f5")
    ink, muted = ("#e6edf8", "#a3b7d5") if dark else ("#344d70", "#596f8e")
    colors = ["#8ca9e8", "#72b9cd", "#a4a9db", "#85baa9", "#c2ad8d", "#a7b6c9"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d UTC")
    frame = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="430" height="248" viewBox="0 0 430 248" role="img">'
        f'<rect x="1" y="1" width="428" height="246" rx="18" fill="{bg}" stroke="{border}"/>'
        f'<g font-family="Arial, sans-serif" fill="{ink}">'
    )
    footer = f'<text x="26" y="226" font-size="11" fill="{muted}">Updated {stamp} · Public, non-fork repositories</text></g></svg>'
    stats = frame + '<title>Public GitHub work</title><text x="26" y="39" font-size="20" font-weight="600">Public GitHub work</text>'
    stats += f'<text x="26" y="64" font-size="12" fill="{muted}">{USER}</text>'
    for x, label, value in zip([26, 160, 294], ["Repositories", "Stars", "Forks"], counts):
        stats += f'<text x="{x}" y="139" font-size="38" font-weight="600" fill="#8ca9e8">{value}</text>'
        stats += f'<text x="{x}" y="167" font-size="13" fill="{muted}">{label}</text>'
    (ASSETS / f"stats-{theme}.svg").write_text(stats + footer, encoding="utf-8")

    code = frame + '<title>Public repository languages by bytes</title><text x="26" y="39" font-size="20" font-weight="600">Language mix</text>'
    code += f'<text x="26" y="64" font-size="12" fill="{muted}">Share of code bytes in public repositories</text>'
    ordered = languages.most_common()
    displayed = ordered[:5]
    if len(ordered) > 5:
        displayed.append(("Other", sum(size for _, size in ordered[5:])))
    total = sum(languages.values())
    position = 26
    for index, (name, size) in enumerate(displayed):
        share = size / total
        width = share * 378
        color = colors[index]
        code += f'<rect x="{position:.2f}" y="87" width="{width:.2f}" height="12" fill="{color}"/>'
        position += width
        x, y = 26 + (index % 2) * 196, 126 + (index // 2) * 29
        code += f'<circle cx="{x + 4}" cy="{y - 4}" r="4" fill="{color}"/>'
        code += f'<text x="{x + 15}" y="{y}" font-size="12">{escape(name)} {share:.1%}</text>'
    if not total:
        code += f'<text x="26" y="135" font-size="13" fill="{muted}">No public code yet — keep building.</text>'
    (ASSETS / f"code-{theme}.svg").write_text(code + footer, encoding="utf-8")


if __name__ == "__main__":
    counts, languages = collect()
    for theme in ("light", "dark"):
        render(counts, languages, theme)
