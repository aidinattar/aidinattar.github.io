#!/usr/bin/env python3
"""Apply the figure filename/path changes to the existing note in place.

Intentionally does NOT ship a replacement note: that could overwrite edits
made recently in Pages CMS. Run once after unpacking the patch.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "synaptic-balance-from-local-rescaling-to-global-order"
NOTE = ROOT / "notes" / f"{SLUG}.md"
SVG = f"/assets/{SLUG}.svg"


def update(source: str) -> tuple[str, list[str]]:
    changes = []
    # Match only the frontmatter's cover image attribute.
    match = re.match(r"\A\ufeff?\+\+\+[ \t]*\r?\n(.*?)\n\+\+\+[ \t]*\r?\n", source, flags=re.S)
    if not match:
        raise ValueError("Expected a +++ frontmatter header in the note")
    head = match.group(1)
    old_image = re.search(r'^image\s*=\s*([\'"])(.*?)\1\s*$', head, re.M)
    if not old_image:
        raise ValueError("No cover image = ... entry in note frontmatter")
    if old_image.group(2) != SVG:
        fixed_head = head[:old_image.start(2)] + SVG + head[old_image.end(2):]
        source = source[:match.start(1)] + fixed_head + source[match.end(1):]
        changes.append("cover image")

    # The note's *visible* Julia code is also the executable source of truth.
    old_save = 'save(joinpath(@OUTPUT, "local-to-global-balancing.svg"), fig)'
    new_save = f'save("{SLUG}.svg", fig)'
    if old_save in source:
        source = source.replace(old_save, new_save, 1)
        changes.append("Julia save() path")
    elif new_save not in source:
        raise ValueError("Expected the original @OUTPUT save() or the updated SVG save() in the Julia code")

    old_img = 'src="/assets/local-to-global-balancing.png"'
    new_img = f'src="{SVG}"'
    if old_img in source:
        source = source.replace(old_img, new_img, 1)
        changes.append("figure image src")
    elif new_img not in source:
        raise ValueError("Could not find the figure image src in the note")

    if not re.search(r"(?m)^```julia[ \t]*$", source):
        raise ValueError("Expected an unescaped ```julia fenced code block in the note")
    return source, changes


def main() -> None:
    if not NOTE.exists():
        raise SystemExit(f"Missing note: {NOTE}")
    old = NOTE.read_text(encoding="utf-8")
    try:
        new, changes = update(old)
    except ValueError as exc:
        raise SystemExit(f"Cannot update {NOTE.name}: {exc}") from exc
    if new != old:
        NOTE.write_text(new, encoding="utf-8")
    print("Updated notes/" + NOTE.name + ": " + (", ".join(changes) if changes else "already up to date"))


if __name__ == "__main__":
    main()
