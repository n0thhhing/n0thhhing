#!/usr/bin/env python3
"""Generates README.md and assets/*.svg. Run: python3 gen.py

GitHub strips CSS from READMEs, so each Material 3 component is an SVG, one per theme.
"""
import json
import math
import os
import pathlib
import random
import textwrap
import urllib.request
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).parent
FONT = "Roboto, ui-sans-serif, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

# Gruvbox Material, medium contrast
THEMES = {
    "dark": dict(
        surface="#282828", container="#32302f", high="#45403d", fg="#d4be98", muted="#a89984",
        red="#ea6962", orange="#e78a4e", yellow="#d8a657", green="#a9b665",
        aqua="#89b482", blue="#7daea3", purple="#d3869b",
    ),
    "light": dict(
        surface="#fbf1c7", container="#f4e8be", high="#ddccab", fg="#654735", muted="#7c6f64",
        red="#c14a4a", orange="#c35e0a", yellow="#b47109", green="#6c782e",
        aqua="#4c7a5d", blue="#45707a", purple="#945e80",
    ),
}

PROJECTS = [
    ("zeon", "Zig", "orange", "ARM and ARM64 Neon intrinsics in pure Zig and inline assembly."),
    ("lwasm", "Lua", "blue", "WebAssembly 2.0 decoder, disassembler, decompiler and interpreter in pure Lua."),
    ("Offset-updater", "TypeScript", "green", "Tracks AArch64 IL2CPP method offsets across binary updates."),
    ("wallify", "Zig", "purple", "macOS desktop music widget, displayed through Kitty."),
    ("ts-capstone", "TypeScript", "aqua", "Capstone disassembly framework bindings for TypeScript."),
    ("Discord-rich-presence", "JavaScript", "red", "Custom Discord Rich Presence over the Gateway API."),
]
LINKS = [
    ("Website", "https://n0thhhing.github.io", True),
    ("GitHub", "https://github.com/n0thhhing?tab=repositories", False),
    ("Instagram", "https://instagram.com/levi.napz", False),
]
STACK = [("Zig", "orange"), ("TypeScript", "blue"), ("Lua", "purple"), ("Kotlin", "green"), ("AArch64", "red")]
LANGUAGE_ACCENTS = ["orange", "blue", "yellow", "purple", "green", "aqua", "red"]
# Fades run in the SVG itself, since a README cannot animate anything else
TWINKLE = (
    "<style>@keyframes tw{0%,100%{opacity:.25}50%{opacity:1}}.tw{animation:tw 4s ease-in-out infinite}"
    "@media (prefers-reduced-motion:reduce){.tw{animation:none}}</style>"
)


def api(path):
    req = urllib.request.Request("https://api.github.com/" + path, headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def fetch_repos():
    # shortcut: reads the first 100 repos only, add paging past that
    return [repo for repo in api("users/n0thhhing/repos?type=owner&per_page=100") if not repo["fork"]]


def fetch_languages(repos):
    totals = {}
    for repo in repos:
        for lang, size in api(f"repos/{repo['full_name']}/languages").items():
            totals[lang] = totals.get(lang, 0) + size
    return totals


def top_languages(totals, n=len(LANGUAGE_ACCENTS)):
    """The n largest languages as (name, percent), with the rest grouped into Other."""
    whole = sum(totals.values())
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    rest = sum(size for _, size in ranked[n:])
    top = ranked[:n] + ([("Other", rest)] if rest else [])
    return [(name, size * 100 / whole) for name, size in top]


def rgb(c):
    return [int(c[i:i + 2], 16) for i in (1, 3, 5)]


def mix(a, b, t):
    return "#%02x%02x%02x" % tuple(round(x * t + y * (1 - t)) for x, y in zip(rgb(a), rgb(b)))


def contrast(a, b):
    def lum(c):
        r, g, b_ = [v / 255 / 12.92 if v / 255 <= 0.03928 else ((v / 255 + 0.055) / 1.055) ** 2.4 for v in rgb(c)]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b_
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def on_tone(t, name):
    """M3 tonal pair for an accent: (container, text), checked to meet WCAG AA."""
    bg = mix(t[name], t["surface"], 0.2)
    text = mix(t[name], t["fg"], 0.3)
    assert contrast(bg, text) >= 4.5, (name, bg, text, contrast(bg, text))
    return bg, text


def svg(w, h, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}" '
        f'font-family="{FONT}">{TWINKLE}{body}</svg>\n'
    )


def text(x, y, s, size, fill, weight=400, anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>'
    )


def sparkle(cx, cy, r, fill, attrs=""):
    """A four-pointed star with concave sides."""
    d = f"M{cx} {cy - r}Q{cx} {cy} {cx + r} {cy}Q{cx} {cy} {cx} {cy + r}Q{cx} {cy} {cx - r} {cy}Q{cx} {cy} {cx} {cy - r}Z"
    return f'<path d="{d}" fill="{fill}" {attrs}/>'


def blossom(cx, cy, r, points, fill, depth=0.08):
    """An M3 Expressive style rounded shape with the given number of lobes."""
    steps = [i * 2 * math.pi / 180 for i in range(180)]
    pts = [(cx + r * (1 + depth * math.cos(points * a)) * math.cos(a), cy + r * (1 + depth * math.cos(points * a)) * math.sin(a)) for a in steps]
    return '<path d="M' + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + f'Z" fill="{fill}"/>'


def tinted(t, accent, w, h, rx):
    """The card surface, with the accent tint growing toward one corner."""
    end = mix(t[accent], t["container"], 0.16)
    return (
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset=".35" stop-color="{t["container"]}"/>'
        f'<stop offset="1" stop-color="{end}"/></linearGradient>'
        f'<rect width="{w}" height="{h}" rx="{rx}" fill="url(#bg)"/>'
    )


def starfield(t, seed, x0, y0, x1, y1, count):
    # Seeded, so the daily workflow only commits when the data changes
    rng = random.Random(seed)
    out = ""
    for _ in range(count):
        color = t[rng.choice(["yellow", "yellow", "fg", "aqua", "orange"])]
        attrs = f'class="tw" style="animation-delay:-{rng.uniform(0, 4):.1f}s"'
        out += sparkle(rng.randint(x0, x1), rng.randint(y0, y1), rng.choice([3, 4, 5, 7, 9]), color, attrs)
    return out


def chip(x, y, label, t, accent):
    # shortcut: width is estimated from character count, since an SVG in <img> cannot measure text
    w = round(len(label) * 7.6 + 28)
    bg, fg = on_tone(t, accent)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="32" rx="16" fill="{bg}"/>'
        + text(x + w / 2, y + 21, label, 13, fg, 500, "middle")
    ), w


def banner(t):
    w, h = 840, 216
    body = (
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="28"/></clipPath></defs>'
        f'<g clip-path="url(#card)">' + tinted(t, "green", w, h, 28)
        + blossom(730, 108, 132, 12, mix(t["green"], t["container"], 0.14))
        + blossom(730, 108, 92, 8, mix(t["yellow"], t["container"], 0.2))
        + starfield(t, 7, 500, 14, 826, 202, 22)
        + sparkle(730, 108, 60, t["yellow"])
        + "</g>"
        + text(40, 80, "Levi", 46, t["fg"], 600)
        + sparkle(152, 46, 13, t["yellow"], 'class="tw"')
        + text(40, 114, "Low-level tools, ARM internals and reverse engineering.", 17, t["muted"])
    )
    x = 40
    for label, accent in STACK:
        c, cw = chip(x, 142, label, t, accent)
        body += c
        x += cw + 8
    return svg(w, h, body, "Levi: low-level tools, ARM internals and reverse engineering")


def card(t, index, name, lang, accent, desc, stars):
    w, h = 412, 172
    bg, fg = on_tone(t, accent)
    body = (
        tinted(t, accent, w, h, 24)
        + sparkle(w - 40, h - 36, 30, t[accent], 'opacity=".22"')
        + starfield(t, index, w - 90, h - 30, w - 14, h - 10, 3)
        + blossom(52, 52, 27, index + 4, bg, 0.1)
        + text(52, 60, name[0].upper(), 22, fg, 500, "middle")
        + text(92, 46, name, 20, t["fg"], 500)
        + text(92, 68, lang, 14, t["muted"])
    )
    if stars:
        label = f"\u2605 {stars}"
        pill = round(len(label) * 8 + 24)
        body += (
            f'<rect x="{w - 20 - pill}" y="24" width="{pill}" height="30" rx="15" fill="{bg}"/>'
            + text(w - 20 - pill / 2, 44, label, 13, fg, 500, "middle")
        )
    for i, line in enumerate(textwrap.wrap(desc, 48)[:3]):
        body += text(24, 120 + i * 22, line, 15, t["fg"])
    alt = f"{name} ({lang}, {stars} stars): {desc}" if stars else f"{name} ({lang}): {desc}"
    return svg(w, h, body, alt)


def languages_card(t, langs):
    w, h = 840, 172
    x, bar_w = 24, w - 48
    colors = [t[LANGUAGE_ACCENTS[i]] if name != "Other" else t["muted"] for i, (name, _) in enumerate(langs)]
    body = (
        tinted(t, "yellow", w, h, 24)
        + f'<clipPath id="bar"><rect x="{x}" y="34" width="{bar_w}" height="16" rx="8"/></clipPath>'
        f'<g clip-path="url(#bar)">'
    )
    for (_, pct), color in zip(langs, colors):
        seg = bar_w * pct / 100
        body += f'<rect x="{x:.1f}" y="34" width="{max(seg - 2, 1):.1f}" height="16" fill="{color}"/>'
        x += seg
    body += "</g>"
    for i, ((name, pct), color) in enumerate(zip(langs, colors)):
        cx, cy = 24 + i % 4 * 200, 88 + i // 4 * 40
        body += (
            sparkle(cx + 7, cy - 5, 9, color)
            + text(cx + 22, cy, name, 15, t["fg"], 500)
            + text(cx + 176, cy, f"{pct:.1f}%", 14, t["muted"], 400, "end")
        )
    return svg(w, h, body, "Languages: " + language_summary(langs))


def language_summary(langs):
    return ", ".join(f"{name} {pct:.1f}%" for name, pct in langs)


def button(t, label, filled):
    w = round(len(label) * 8.6 + (66 if filled else 48))
    bg, fg = (mix(t["green"], t["fg"], 0.6), t["surface"]) if filled else (t["high"], t["fg"])
    assert contrast(bg, fg) >= 4.5, (label, bg, fg)
    body = f'<rect width="{w}" height="40" rx="20" fill="{bg}"/>'
    if filled:
        body += sparkle(26, 20, 8, fg) + text(40, 25, label, 14, fg, 500)
    else:
        body += text(w / 2, 25, label, 14, fg, 500, "middle")
    return svg(w, 40, body, label)


def picture(name, alt, attrs):
    return (
        f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
        f'<img src="assets/{name}-light.svg" alt="{escape(alt)}" {attrs}></picture>'
    )


def readme(langs):
    out = ['<p align="center">' + picture("banner", "Levi: low-level tools, ARM internals and reverse engineering", 'width="100%"') + "</p>\n"]
    links = "\n".join(
        '  <a href="%s">%s</a>' % (url, picture("link-" + label.lower(), label, 'height="40"'))
        for label, url, _ in LINKS
    )
    out.append(f'<p align="center">\n{links}\n</p>\n')
    out.append("### \u2726 Projects\n")
    for i in range(0, len(PROJECTS), 2):
        cells = "\n".join(
            '  <a href="https://github.com/n0thhhing/%s">%s</a>'
            % (name, picture("project-" + name.lower(), f"{name}: {desc}", 'width="49%"'))
            for name, _, _, desc in PROJECTS[i:i + 2]
        )
        out.append(f'<p align="center">\n{cells}\n</p>\n')
    out.append("### \u2726 Languages\n")
    out.append('<p align="center">' + picture("languages", "Languages: " + language_summary(langs), 'width="100%"') + "</p>\n")
    return "\n".join(out)


def main():
    assert top_languages({"a": 3, "b": 1}, 1) == [("a", 75.0), ("Other", 25.0)]
    repos = fetch_repos()
    langs = top_languages(fetch_languages(repos))
    stars = {repo["name"]: repo["stargazers_count"] for repo in repos}
    (ROOT / "assets").mkdir(exist_ok=True)
    for mode, t in THEMES.items():
        files = {"banner": banner(t), "languages": languages_card(t, langs)}
        for i, (name, lang, accent, desc) in enumerate(PROJECTS):
            files["project-" + name.lower()] = card(t, i, name, lang, accent, desc, stars.get(name, 0))
        for label, _, filled in LINKS:
            files["link-" + label.lower()] = button(t, label, filled)
        for name, content in files.items():
            (ROOT / "assets" / f"{name}-{mode}.svg").write_text(content)
    (ROOT / "README.md").write_text(readme(langs))


if __name__ == "__main__":
    main()
