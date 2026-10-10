#!/usr/bin/env python3
"""Stop deployment if Franklin silently skips a published note (404 regression)."""
from pathlib import Path
from normalize_notes import NOTES, ROOT, read_note

SITE = ROOT / '__site'
issues = []
count = 0

for source in sorted(NOTES.glob('*.md')):
    meta, _, _ = read_note(source)
    if not meta.get('published', True):
        continue
    count += 1
    page = SITE / 'notes' / source.stem / 'index.html'
    if not page.is_file():
        issues.append(f'Missing published page: {page.relative_to(ROOT)} ({source.relative_to(ROOT)})')
    if meta.get('image'):
        image = SITE / str(meta['image']).lstrip('/')
        if str(meta['image']).startswith('/assets/') and not image.is_file():
            issues.append(f'Missing deployed cover image: {image.relative_to(ROOT)} ({source.relative_to(ROOT)})')

if issues:
    raise SystemExit('Site verification failed:\n' + '\n'.join(f'  - {issue}' for issue in issues))
print(f'Site verification passed: {count} published note pages and cover images checked.')
