"""Generate assets/stats.svg from the GitHub API (run daily by Actions)."""
import json, os, sys, urllib.request
from collections import Counter

user = os.environ.get("GH_USER", "ODAY8")
token = os.environ.get("GITHUB_TOKEN")

def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

profile = api(f"/users/{user}")
repos, page = [], 1
while True:
    batch = api(f"/users/{user}/repos?per_page=100&type=owner&page={page}")
    repos += batch
    if len(batch) < 100:
        break
    page += 1
own = [r for r in repos if not r["fork"]]
stars = sum(r["stargazers_count"] for r in own)
langs = Counter(r["language"] for r in own if r["language"])
total = sum(langs.values()) or 1

COLORS = ["#4FD1C5", "#63B3ED", "#F6AD55", "#B794F4", "#FC8181", "#68D391"]
F = "font-family=\"'Segoe UI',Helvetica,Arial,sans-serif\""
stats = [("Public repos", profile["public_repos"]), ("Stars earned", stars), ("Followers", profile["followers"])]

parts = []
for i, (label, val) in enumerate(stats):
    x = 40 + i * 270
    parts.append(f'<text x="{x}" y="62" {F} font-size="36" font-weight="700" fill="#FFFFFF">{val}</text>'
                 f'<text x="{x}" y="86" {F} font-size="13" fill="#8B949E">{label}</text>')

bar, legend, x = [], [], 40
for i, (lang, n) in enumerate(langs.most_common(6)):
    w = max(4, 820 * n / total)
    bar.append(f'<rect x="{x:.1f}" y="118" width="{w:.1f}" height="10" fill="{COLORS[i % 6]}"/>')
    x += w
    lx = 40 + i * 135
    legend.append(f'<circle cx="{lx+5}" cy="153" r="5" fill="{COLORS[i % 6]}"/>'
                  f'<text x="{lx+16}" y="157" {F} font-size="12" fill="#C9D1D9">{lang} {round(100*n/total)}%</text>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="180" viewBox="0 0 900 180" role="img" aria-label="GitHub statistics for {user}">
<defs><clipPath id="r"><rect x="40" y="118" width="820" height="10" rx="5"/></clipPath></defs>
<rect width="900" height="180" rx="14" fill="#0D1117" stroke="#30363D"/>
{''.join(parts)}
<g clip-path="url(#r)">{''.join(bar)}</g>
{''.join(legend)}
</svg>'''
os.makedirs("assets", exist_ok=True)
open("assets/stats.svg", "w").write(svg)
print("stats:", stats, dict(langs))
