#!/usr/bin/env python3
"""Make Pages CMS TOML note headers compatible with Franklin's Julia headers.

Pages CMS can output valid TOML literal strings ('like this'); Franklin's +++
headers are Julia expressions and require Julia-compatible string syntax.

This script touches only a note's +++ header, unless --repair-image-paths is
explicitly requested. It never modifies the actual prose, code or math.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import tomllib
from datetime import date, datetime, time
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / 'notes'
ASSETS = ROOT / '_assets'

FRONTMATTER = re.compile(r'\A(\ufeff?\+\+\+[ \t]*\r?\n)(?P<header>.*?)(\r?\n\+\+\+[ \t]*(?:\r?\n|\Z))', re.S)
MARKDOWN_IMAGE = re.compile(r'!\[[^\]]*\]\(\s*(?P<path>/?assets/[^\s)]+)', re.I)
HTML_IMAGE = re.compile(r'<img\b[^>]*\bsrc\s*=\s*["\'](?P<path>/assets/[^"\']+)["\']', re.I | re.S)


def julia_literal(value: object) -> str:
    """Produce Julia-compatible literals for the Page CMS supported TOML types."""
    if isinstance(value, str):
        # Escape $ as Unicode for Julia (no interpolation) and TOML (also valid).
        return json.dumps(value, ensure_ascii=False).replace('$', r'\u0024')
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('infinite and NaN numbers are not supported')
        return repr(value)
    if isinstance(value, list):
        return '[' + ', '.join(julia_literal(v) for v in value) + ']'
    if isinstance(value, (date, datetime, time)):
        raise ValueError('unquoted TOML dates are unsupported; set Date to a quoted string')
    raise ValueError(f'unsupported frontmatter type: {type(value).__name__}')


def read_note(path: Path) -> tuple[dict, str, re.Match[str]]:
    source = path.read_text(encoding='utf-8')
    match = FRONTMATTER.match(source)
    if not match:
        raise ValueError(f'{path.relative_to(ROOT)}: missing +++ frontmatter')
    try:
        meta = tomllib.loads(match.group('header'))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f'{path.relative_to(ROOT)}: invalid TOML frontmatter: {exc}') from exc
    for key, value in meta.items():
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', key):
            raise ValueError(f'{path.relative_to(ROOT)}: invalid Franklin variable name {key!r}')
        try:
            julia_literal(value)
        except ValueError as exc:
            raise ValueError(f'{path.relative_to(ROOT)}: {key}: {exc}') from exc
    if not isinstance(meta.get('published', True), bool):
        raise ValueError(f'{path.relative_to(ROOT)}: published must be a boolean')
    if 'topics' in meta and (not isinstance(meta['topics'], list) or
                             any(not isinstance(t, str) for t in meta['topics'])):
        raise ValueError(f'{path.relative_to(ROOT)}: topics must be a list of strings')
    return meta, source, match


def local_asset_path(webpath: str) -> Path | None:
    """Map a local /assets/... reference to the actual tracked _assets/... file."""
    raw = webpath.strip().strip('"\'')
    route = urlsplit(raw)
    if route.scheme or route.netloc or not route.path.startswith('/assets/'):
        return None
    relative = unquote(route.path[len('/assets/'):])
    dest = (ASSETS / relative).resolve()
    if not dest.is_relative_to(ASSETS.resolve()):
        raise ValueError(f'unsafe image path {webpath!r}')
    return dest


def check_images(path: Path, meta: dict, body: str, repair: bool = False) -> str:
    """Check local images; optionally repair unambiguous old image links.

    Repair only when a missing body image has the same basename as an existing
    cover image selected in the CMS. Anything ambiguous is an explicit error.
    """
    images = []
    if meta.get('image'):
        images.append(('image field', str(meta['image'])))
    for expr in (MARKDOWN_IMAGE, HTML_IMAGE):
        images.extend(('body', m.group('path')) for m in expr.finditer(body))

    for where, address in images:
        asset = local_asset_path(address)
        if asset is None:
            continue
        if asset.is_file():
            continue
        cover_address = str(meta.get('image') or '')
        cover = local_asset_path(cover_address)
        if (repair and where == 'body' and cover is not None and cover.is_file()
                and cover.name == asset.name):
            print(f'{path.relative_to(ROOT)}: repair missing body image {address} -> {cover_address}')
            body = body.replace(address, cover_address)
            continue
        raise ValueError(
            f'{path.relative_to(ROOT)}: missing image {address!r} ({where}). '
            'CMS media is saved under _assets/ and served at /assets/. '
            'Upload the missing image or correct its path.'
        )
    return body


def normalize_one(path: Path, repair_image_paths: bool = False) -> tuple[dict, bool]:
    meta, source, match = read_note(path)
    frontmatter = '\n'.join(f'{key} = {julia_literal(value)}' for key, value in meta.items())
    body = source[match.end():]
    if meta.get('published', True):
        body = check_images(path, meta, body, repair_image_paths)
    newline = '\r\n' if '\r\n' in match.group(0) else '\n'
    new_text = (match.group(1) + frontmatter.replace('\n', newline)
                + newline + '+++' + newline + body)
    changed = new_text != source
    if changed:
        path.write_text(new_text, encoding='utf-8')
    return meta, changed


def normalize_all(repair_image_paths: bool = False) -> tuple[int, int]:
    converted = 0
    total = 0
    for source in sorted(NOTES.glob('*.md')):
        _, changed = normalize_one(source, repair_image_paths)
        total += 1
        converted += changed
        if changed:
            print(f'Normalized {source.relative_to(ROOT)}')
    return total, converted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repair-image-paths', action='store_true',
                        help='Repair missing body images when they match an existing cover image by filename')
    args = parser.parse_args()
    n, c = normalize_all(args.repair_image_paths)
    print(f'Checked {n} notes; normalized {c}.')


if __name__ == '__main__':
    main()
