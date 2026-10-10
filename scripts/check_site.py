#!/usr/bin/env python3
"""Verify every published note has a page and a working index entry."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from normalize_notes import NOTES, ROOT, read_note

SITE = ROOT / '__site'


class IndexLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != 'a':
            return
        for key, value in attrs:
            if key == 'href' and value:
                self.hrefs.add(urlsplit(value).path.rstrip('/') + '/')


def check_notes() -> tuple[int, list[str]]:
    issues: list[str] = []
    published = []
    for source in sorted(NOTES.glob('*.md')):
        meta, _, _ = read_note(source)
        if not meta.get('published', True):
            continue
        published.append(source)
        page = SITE / 'notes' / source.stem / 'index.html'
        if not page.is_file():
            issues.append(f'Missing published page: {page.relative_to(ROOT)} ({source.relative_to(ROOT)})')
        if meta.get('image'):
            address = str(meta['image'])
            if address.startswith('/assets/'):
                image = SITE / address.lstrip('/')
                if not image.is_file():
                    issues.append(f'Missing deployed cover image: {image.relative_to(ROOT)} ({source.relative_to(ROOT)})')

    index = SITE / 'notes' / 'index.html'
    if not index.is_file():
        issues.append('Missing Notes index: __site/notes/index.html')
    else:
        parser = IndexLinks()
        parser.feed(index.read_text(encoding='utf-8'))
        for source in published:
            route = '/notes/' + source.stem + '/'
            if route not in parser.hrefs:
                issues.append(f'Published note absent from Notes index: {route}')
    return len(published), issues


if __name__ == '__main__':
    count, errors = check_notes()
    if errors:
        raise SystemExit('Site verification failed:\n' + '\n'.join(f'  - {issue}' for issue in errors))
    print(f'Site verification passed: {count} published note pages, links, and cover images checked.')
