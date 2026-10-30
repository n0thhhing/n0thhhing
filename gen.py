#!/usr/bin/env python3
"""Generates README.md and assets/*.svg. Run: python3 gen.py

GitHub strips CSS from READMEs, so each Material 3 component is an SVG, one per theme.
"""
import pathlib
import textwrap
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
        f'font-family="{FONT}">{body}</svg>\n'
    )


def text(x, y, s, size, fill, weight=400, anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>'
    )


def chip(x, y, label, t, accent):
    # shortcut: width is estimated from character count, since an SVG in <img> cannot measure text
    w = round(len(label) * 7.6 + 28)
    bg, fg = on_tone(t, accent)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="32" rx="8" fill="{bg}"/>'
        + text(x + w / 2, y + 21, label, 13, fg, 500, "middle")
    ), w


def banner(t):
    w, h = 840, 216
    body = (
        f'<defs><clipPath id="card"><rect width="{w}" height="{h}" rx="28"/></clipPath></defs>'
        f'<g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="{t["container"]}"/>'
        f'<circle cx="790" cy="20" r="150" fill="{mix(t["green"], t["container"], 0.16)}"/>'
        f'<circle cx="690" cy="220" r="84" fill="{mix(t["orange"], t["container"], 0.16)}"/></g>'
        + text(40, 80, "Levi", 44, t["fg"], 500)
        + text(40, 114, "Low-level tools, ARM internals and reverse engineering.", 17, t["muted"])
    )
    x = 40
    for label, accent in STACK:
        c, cw = chip(x, 142, label, t, accent)
        body += c
        x += cw + 8
    return svg(w, h, body, "Levi: low-level tools, ARM internals and reverse engineering")


def card(t, name, lang, accent, desc):
    w, h = 412, 160
    bg, fg = on_tone(t, accent)
    body = (
        f'<rect width="{w}" height="{h}" rx="24" fill="{t["container"]}"/>'
        f'<circle cx="48" cy="48" r="24" fill="{bg}"/>'
        + text(48, 56, name[0].upper(), 22, fg, 500, "middle")
        + text(84, 42, name, 20, t["fg"], 500)
        + text(84, 64, lang, 14, t["muted"])
    )
    for i, line in enumerate(textwrap.wrap(desc, 48)[:3]):
        body += text(24, 112 + i * 22, line, 15, t["fg"])
    return svg(w, h, body, f"{name} ({lang}): {desc}")


def button(t, label, filled):
    w = round(len(label) * 8.6 + 48)
    bg, fg = (mix(t["green"], t["fg"], 0.6), t["surface"]) if filled else (t["high"], t["fg"])
    assert contrast(bg, fg) >= 4.5, (label, bg, fg)
    body = f'<rect width="{w}" height="40" rx="20" fill="{bg}"/>' + text(w / 2, 25, label, 14, fg, 500, "middle")
    return svg(w, 40, body, label)


def picture(name, alt, attrs):
    return (
        f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
        f'<img src="assets/{name}-light.svg" alt="{escape(alt)}" {attrs}></picture>'
    )


def readme():
    out = ['<p align="center">' + picture("banner", "Levi: low-level tools, ARM internals and reverse engineering", 'width="100%"') + "</p>\n"]
    links = "\n".join(
        '  <a href="%s">%s</a>' % (url, picture("link-" + label.lower(), label, 'height="40"'))
        for label, url, _ in LINKS
    )
    out.append(f'<p align="center">\n{links}\n</p>\n')
    out.append("### Projects\n")
    for i in range(0, len(PROJECTS), 2):
        cells = "\n".join(
            '  <a href="https://github.com/n0thhhing/%s">%s</a>'
            % (name, picture("project-" + name.lower(), f"{name}: {desc}", 'width="49%"'))
            for name, _, _, desc in PROJECTS[i:i + 2]
        )
        out.append(f'<p align="center">\n{cells}\n</p>\n')
    return "\n".join(out)


def main():
    (ROOT / "assets").mkdir(exist_ok=True)
    for mode, t in THEMES.items():
        files = {"banner": banner(t)}
        for name, lang, accent, desc in PROJECTS:
            files["project-" + name.lower()] = card(t, name, lang, accent, desc)
        for label, _, filled in LINKS:
            files["link-" + label.lower()] = button(t, label, filled)
        for name, content in files.items():
            (ROOT / "assets" / f"{name}-{mode}.svg").write_text(content)
    (ROOT / "README.md").write_text(readme())


if __name__ == "__main__":
    main()
