
import os
import json
import html
import re
import urllib.request
import urllib.error
from pathlib import Path
from datetime import date

USERNAME = "XiaozheQAQ"
TOKEN = os.environ.get("CONTRIBUTION_TOKEN")

if not TOKEN:
    raise RuntimeError("Missing CONTRIBUTION_TOKEN")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            weekday
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {"login": USERNAME}
}).encode("utf-8")

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "XiaozheQAQ-Contribution-Graph"
    }
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    raise RuntimeError(
        f"GitHub API error: {e.code} {e.read().decode('utf-8')}"
    )

if result.get("errors"):
    raise RuntimeError(result["errors"])

calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]

weeks = calendar["weeks"]
total = calendar["totalContributions"]

CELL = 11
GAP = 3
STEP = CELL + GAP

LEFT = 40
TOP = 42

WIDTH = LEFT + len(weeks) * STEP + 5
HEIGHT = TOP + 7 * STEP + 8

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{WIDTH}" height="{HEIGHT}" '
    f'viewBox="0 0 {WIDTH} {HEIGHT}">',
    '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">',
    f'<text x="{LEFT}" y="16" font-size="12" '
    f'fill="#6e7781">{total} contributions in the last year</text>'
]

# 月份标签
for i, week in enumerate(weeks):
    for day in week["contributionDays"]:
        if day["date"][8:10] == "01":
            month = date.fromisoformat(
                day["date"]
            ).strftime("%b")

            svg.append(
                f'<text x="{LEFT + i * STEP}" y="35" '
                f'font-size="9" fill="#6e7781">{month}</text>'
            )
            break

# 星期标签
for weekday, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
    y = TOP + weekday * STEP + 9
    svg.append(
        f'<text x="2" y="{y}" font-size="9" '
        f'fill="#6e7781">{label}</text>'
    )

# 贡献方格
for i, week in enumerate(weeks):
    for day in week["contributionDays"]:
        x = LEFT + i * STEP
        y = TOP + int(day["weekday"]) * STEP

        color = day["color"]

        # 避免使用非预期颜色值
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            color = "#ebedf0"

        count = day["contributionCount"]
        date_text = html.escape(day["date"])

        svg.append(
            f'<rect x="{x}" y="{y}" '
            f'width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{color}">'
            f'<title>{date_text}: {count} contributions</title>'
            f'</rect>'
        )

svg.append("</g></svg>")

output = Path("assets/contributions.svg")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(svg), encoding="utf-8")

print(f"Generated {output}, total contributions: {total}")
