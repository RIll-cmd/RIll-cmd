"""Generate the retro / neobrutalist SVGs for the GitHub profile README.

Run: GITHUB_TOKEN=... python gen.py   (the daily workflow does this)
"""
import json
import os
import textwrap
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape

LOGIN = "RIll-cmd"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Restrained palette: ink, paper, one yellow accent, greys.
INK, CREAM, SCREEN = "#111111", "#FFF8E7", "#16161D"
ACCENT, WHITE, GREY, LIGHT, TRACK = "#FFD23F", "#FFFFFF", "#9AA0A6", "#C9CDD2", "#E5DCC8"
DARK = "@media (prefers-color-scheme: dark){.sh{fill:#E6EDF3}}"  # hard shadow stays visible on dark GitHub
MONO = "'Courier New', ui-monospace, monospace"

# 5x7 bitmap font, one string per row.
FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111",
    "+": "00000 00100 00100 11111 00100 00100 00000",
    "=": "00000 00000 11111 00000 11111 00000 00000",
    ">": "01000 00100 00010 00001 00010 00100 01000",
    "<": "00010 00100 01000 10000 01000 00100 00010",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00010 00100 00000 00100",
    "&": "01100 10010 10100 01000 10101 10010 01101",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "|": "00100 00100 00100 00100 00100 00100 00100",
    "'": "00100 00100 01000 00000 00000 00000 00000",
    "%": "11001 11010 00010 00100 01000 01011 10011",
    "#": "01010 01010 11111 01010 11111 01010 01010",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    "*": "00100 00100 11111 01110 01110 11011 10001",  # star
}

ROBOT = """
....XXXXXX....
...X......X...
..X.XX..XX.X..
..X.XX..XX.X..
..X........X..
..X..XXXX..X..
...X......X...
....XXXXXX....
..XX.X..X.XX..
.X...XXXX...X.
.....X..X.....
....XX..XX....
""".split()


def pixels_to_path(cells):
    return "".join(f"M{x} {y}h1v1h-1z" for x, y in cells)


def text_cells(text):
    cells = []
    for i, ch in enumerate(text.upper()):
        rows = FONT.get(ch, "00000 " * 7).split()
        cells += [(i * 6 + x, y) for y, row in enumerate(rows) for x, b in enumerate(row) if b == "1"]
    return cells


def px(text, x, y, s, fill, extra=""):
    """Pixel-font text; each glyph is 6*s wide, 7*s tall."""
    return (f'<path transform="translate({x} {y}) scale({s})" fill="{fill}" {extra} '
            f'd="{pixels_to_path(text_cells(text))}"/>')


def px_w(text, s):
    return (len(text) * 6 - 1) * s


def box(x, y, w, h, fill, sw=4, shadow=8):
    """Neobrutalist box: hard offset shadow + thick ink border."""
    return (f'<rect class="sh" x="{x + shadow}" y="{y + shadow}" width="{w}" height="{h}" fill="{INK}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{INK}" stroke-width="{sw}"/>')


def tag(x, y, label, fill, stroke=INK, text=INK):
    tw = px_w(label, 2)
    return (f'<rect x="{x}" y="{y}" width="{tw + 20}" height="28" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'
            + px(label, x + 10, y + 7, 2, text)), tw + 20


def svg(w, h, body, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'shape-rendering="crispEdges"><style>{DARK}{style}</style>{body}</svg>\n')


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)


def gql(query, **variables):
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-gen"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


# ---------------------------------------------------------------- data

USER_Q = """query($login:String!){ user(login:$login){
  createdAt followers{totalCount}
  contributionsCollection{ contributionCalendar{ totalContributions } }
  repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){
    totalCount
    nodes{ name stargazerCount primaryLanguage{name}
      languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } } } }
  wake: repository(owner:"sutayniee", name:"Wake-Brake"){ name stargazerCount primaryLanguage{name} } }"""

LISTS_Q = """query($login:String!){ user(login:$login){
  lists(first:10){ nodes{ name slug description items(first:1){ totalCount } } } } }"""

# Fallback if the token can't read star lists (shortcut: counts go stale; update by hand if that happens).
LISTS_FALLBACK = [
    {"name": "FlyRank", "slug": "flyrank", "description": "My Assignments and Capstones on FlyRank AI Internship", "items": {"totalCount": 21}},
    {"name": "Projects & Prototypes", "slug": "projects-prototypes", "description": "Experiments and Future Projects", "items": {"totalCount": 4}},
    {"name": "Software Engineering Showcase", "slug": "software-engineering-showcase", "description": "My personal projects spanning systems programming, edge AI, IoT, and real-time behavioral analysis.", "items": {"totalCount": 3}},
    {"name": "Thesis", "slug": "thesis", "description": "Tri-modal embedded driver safety and fatigue monitoring system combining edge computer vision, real-time drowsiness detection, and low-latency hardware actuation", "items": {"totalCount": 2}},
]

# (repo, owner/repo if not mine, extra tag, blurb)
PROJECTS = [
    ("ascend-hub", None, None, "Orchestrator for AI coding agents. Codex, Claude and Antigravity plan, build, review and merge as a team behind approval gates, with a retro status dashboard."),
    ("ascend-core", None, None, "Gamified self-mastery platform that turns workouts, habits, focus, sleep and personal goals into structured progression, powered by AI."),
    ("ascend-vision", None, None, "Computer-vision and gesture-control layer combining MediaPipe, YOLO, focus tracking, local analytics and conversational AI feedback."),
    ("Wake-Brake", "sutayniee/Wake-Brake", "THESIS", "Driver fatigue detection system running multiple algorithms on a Raspberry Pi, with an Arduino-driven haptic actuator for alerts."),
    ("Kinsenas-Collection-Agent", None, None, "AI collections agent for Philippine small businesses, built on n8n. Payday-timed reminders, Gemini reply handling, Telegram approvals and receipt checks."),
    ("prescriptive-finance", None, None, "AI financial operating system for young Filipinos: financial health scoring, safe-to-spend limits, adaptive savings and purchase simulations."),
]
LANG_OVERRIDE = {"Kinsenas-Collection-Agent": "n8n"}


# ---------------------------------------------------------------- art

BLINK = "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:blink 1s steps(1) infinite}"


def banner():
    w, h = 900, 300
    style = (BLINK + "@keyframes bob{0%,49%{transform:translateY(0)}50%,100%{transform:translateY(-6px)}}"
             ".bob{animation:bob 1.4s steps(1) infinite}")
    b = [
        '<defs><pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#ffffff" opacity=".05"/></pattern></defs>',
        box(4, 4, 876, 276, ACCENT, sw=5, shadow=12),
        px("RILL-CMD", 22, 17, 2, INK),
    ]
    for i in range(3):
        b.append(f'<rect x="{776 + i * 32}" y="14" width="22" height="22" fill="{WHITE}" stroke="{INK}" stroke-width="3"/>')
    b.append(px("X", 845, 18, 2, INK))
    b.append(f'<rect x="4" y="46" width="876" height="4" fill="{INK}"/>')
    b.append(f'<rect x="22" y="64" width="840" height="196" fill="{SCREEN}" stroke="{INK}" stroke-width="4"/>')
    b.append(px("HELLO, I'M", 46, 86, 2, GREY))
    name = "CYRILL GERARD CAJUCOM"
    b.append(px(name, 50, 116, 4, "#4A3F12"))
    b.append(px(name, 46, 112, 4, WHITE))
    role = "COMPUTER SCIENCE STUDENT"
    b.append(px(role, 46, 160, 2, ACCENT))
    b.append(f'<rect class="blink" x="{46 + px_w(role, 2) + 8}" y="160" width="10" height="14" fill="{ACCENT}"/>')
    b.append(px("BSCS, SOFTWARE ENGINEERING | FEU TECH | MANILA, PH", 46, 184, 2, LIGHT))
    x = 46
    for label in ["FASTAPI", "MULTI-AGENT TOOLS", "EDGE CV", "PI / ARDUINO"]:
        t, tw = tag(x, 216, label, SCREEN, stroke=GREY, text=LIGHT)
        b.append(t)
        x += tw + 12
    robot = [(x, y) for y, row in enumerate(ROBOT) for x, c in enumerate(row) if c == "X"]
    b.append(f'<g transform="translate(712 100)"><g class="bob">'
             f'<path transform="scale(8)" fill="{LIGHT}" d="{pixels_to_path(robot)}"/></g></g>')
    b.append(f'<rect x="22" y="64" width="840" height="196" fill="url(#scan)"/>')
    write("banner.svg", svg(w, h, "".join(b), style))


def header(slug, text):
    s = 3
    tw = px_w(text, s)
    w, h = tw + 48 + 10, 21 + 24 + 10
    write(f"h-{slug}.svg", svg(w, h, box(2, 2, tw + 44, 21 + 20, ACCENT, shadow=6) + px(text, 24, 12, s, INK)))


def card(repo, extra, blurb, stars, lang):
    w, h = 460, 230
    title = "WAKE&BRAKE" if repo == "Wake-Brake" else repo.upper()
    s = 3 if px_w(title, 3) <= 380 else 2
    b = [box(4, 4, 444, 214, CREAM, shadow=8),
         f'<rect x="4" y="4" width="444" height="52" fill="{INK}" stroke="{INK}" stroke-width="4"/>',
         px(title, 22, 30 - 7 * s // 2, s, WHITE)]
    for i, line in enumerate(textwrap.wrap(blurb, 46)[:4]):
        b.append(f'<text x="22" y="{86 + i * 22}" font-family="{MONO}" font-size="15" font-weight="700" '
                 f'fill="{INK}">{escape(line)}</text>')
    x = 22
    for label, fill in [(lang.upper(), WHITE), (f"* {stars}", ACCENT)] + ([(extra, WHITE)] if extra else []):
        t, tw = tag(x, 176, label, fill)
        b.append(t)
        x += tw + 12
    write(f"quest-{repo.lower()}.svg", svg(w, h, "".join(b)))


def save_slot(i, lst):
    w, h = 460, 120
    count = lst["items"]["totalCount"]
    b = [box(4, 4, 444, 104, WHITE, shadow=8),
         f'<rect x="4" y="4" width="92" height="104" fill="{INK}" stroke="{INK}" stroke-width="4"/>',
         px("LIST", 26, 30, 2, GREY), px(f"{i:02d}", 26, 54, 4, ACCENT),
         px(lst["name"].upper(), 114, 26, min(2, 316 / px_w(lst["name"], 1)), INK),
         px(f"{count} REPOSITORIES", 114, 50, 2, "#555555")]
    desc = textwrap.shorten(lst.get("description") or "", 42, placeholder="...")
    b.append(f'<text x="114" y="90" font-family="{MONO}" font-size="13" font-weight="700" fill="{INK}">{escape(desc)}</text>')
    write(f"save-{lst['slug']}.svg", svg(w, h, "".join(b)))


def stats(user):
    w, h = 900, 290
    repos = user["repositories"]["nodes"]
    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    years = max(1, (datetime.now(timezone.utc) - created).days // 365 + 1)
    rows = [("YEARS ON GITHUB", years), ("PUBLIC REPOSITORIES", user["repositories"]["totalCount"]),
            ("TOTAL STARS", sum(r["stargazerCount"] for r in repos)),
            ("FOLLOWERS", user["followers"]["totalCount"]),
            ("CONTRIBUTIONS (1Y)", user["contributionsCollection"]["contributionCalendar"]["totalContributions"])]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]

    b = [box(4, 4, 876, 266, CREAM, shadow=10),
         f'<rect x="4" y="4" width="876" height="48" fill="{INK}" stroke="{INK}" stroke-width="4"/>',
         px("GITHUB STATS", 24, 21, 2, WHITE),
         px("UPDATED " + datetime.now(timezone.utc).strftime("%Y-%m-%d"), 856 - px_w("UPDATED 0000-00-00", 2), 21, 2, GREY),
         f'<rect x="452" y="68" width="4" height="186" fill="{INK}"/>']
    for i, (label, val) in enumerate(rows):
        y = 76 + i * 36
        b.append(px(label, 26, y, 2, INK))
        v = str(val)
        b.append(px(v, 426 - px_w(v, 3), y - 4, 3, INK))
    b.append(px("TOP LANGUAGES", 480, 76, 2, INK))
    for i, (name, size) in enumerate(top):
        y = 108 + i * 30
        pct = size / total * 100
        b.append(px(name.upper()[:10], 480, y, 2, INK))
        on = max(1, round(pct / 5))
        for s in range(20):
            fill = (ACCENT if i == 0 else INK) if s < on else TRACK
            b.append(f'<rect x="{620 + s * 10}" y="{y}" width="8" height="14" fill="{fill}" stroke="{INK}" stroke-width="1"/>')
        b.append(px(f"{pct:.0f}%", 830, y, 2, INK))
    write("stats.svg", svg(w, h, "".join(b)))


def footer():
    w, h = 900, 80
    site = "CAJUCOMPORTFOLIO.VERCEL.APP"
    b = [box(4, 4, 876, 60, SCREEN, shadow=8),
         px("THANK YOU FOR VISITING", 28, 27, 2, WHITE),
         px(site, 852 - px_w(site, 2), 27, 2, ACCENT)]
    write("footer.svg", svg(w, h, "".join(b)))


def main():
    os.makedirs(OUT, exist_ok=True)
    data = gql(USER_Q, login=LOGIN)
    user = data["user"]
    try:
        lists = gql(LISTS_Q, login=LOGIN)["user"]["lists"]["nodes"] or LISTS_FALLBACK
    except Exception as e:  # GITHUB_TOKEN in Actions may not see star lists
        print("lists fallback:", e)
        lists = LISTS_FALLBACK

    by_name = {r["name"]: r for r in user["repositories"]["nodes"]}
    for repo, other, extra, blurb in PROJECTS:
        r = data["wake"] if other == "sutayniee/Wake-Brake" else by_name.get(repo, {})
        lang = LANG_OVERRIDE.get(repo) or ((r.get("primaryLanguage") or {}).get("name")) or "code"
        card(repo, extra, blurb, r.get("stargazerCount", 0), lang)

    for i, lst in enumerate(lists, 1):
        lst["name"] = lst["name"].encode("ascii", "ignore").decode().strip()  # drop emoji, font is ASCII
        save_slot(i, lst)

    banner()
    stats(user)
    footer()
    for slug, text in [("about", "> ABOUT"), ("inventory", "> TECH STACK"), ("quests", "> FEATURED PROJECTS"),
                       ("saves", "> COLLECTIONS"), ("stats", "> GITHUB STATS"), ("snake", "> CONTRIBUTIONS")]:
        header(slug, text)
    assert os.path.getsize(os.path.join(OUT, "banner.svg")) > 1000
    print("ok:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
