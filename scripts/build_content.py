#!/usr/bin/env python3
"""Build HTML lists from Pages CMS content without altering the original pages.

Only Python's standard library is required. Run before Franklin.optimize()/serve().
The notes/*.md files are the canonical Pages CMS and Franklin sources.
"""
from __future__ import annotations

import html
import json
import re
import tomllib
from pathlib import Path
from urllib.parse import urlparse

from normalize_notes import normalize_all

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'content'
LAYOUT = ROOT / '_layout' / 'generated'
NOTES = ROOT / 'notes'
LAYOUT.mkdir(parents=True, exist_ok=True)


def e(value: object) -> str:
    return html.escape(str(value if value is not None else ''), quote=True)


def url(value: object) -> str:
    """Reject URL schemes unsafe for CMS-derived href/src attributes."""
    raw = str(value or '').strip()
    parts = urlparse(raw)
    if parts.scheme in ('https', 'http') and parts.netloc:
        return e(raw)
    if raw.startswith('/') and not raw.startswith('//') and not raw.startswith('/\\'):
        return e(raw)
    return ''


def items(folder: str) -> list[dict]:
    result = []
    for path in sorted((DATA / folder).glob('*.json')):
        try:
            obj = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as err:
            raise ValueError(f'Invalid JSON in {path}: {err}') from err
        if not isinstance(obj, dict):
            raise ValueError(f'{path} must contain a JSON object')
        obj['_slug'] = path.stem
        result.append(obj)
    return result


def write(name: str, output: str) -> None:
    (LAYOUT / name).write_text(output.rstrip() + '\n', encoding='utf-8')


def compact_link(label: str, href: object, cls: str = '') -> str:
    safe_href = url(href)
    if not safe_href:
        return ''
    classes = f' class="{cls}"' if cls else ''
    return f'<a href="{safe_href}"{classes} target="_blank" rel="noopener noreferrer">{e(label)}</a>'


def pub_links(item: dict) -> str:
    links = []
    if item.get('doi'):
        doi = str(item['doi']).replace('https://doi.org/', '').strip()
        links.append(compact_link('DOI', f'https://doi.org/{doi}'))
    if item.get('arxiv'):
        arxiv = str(item['arxiv']).replace('https://arxiv.org/abs/', '').strip()
        links.append(compact_link('arXiv', f'https://arxiv.org/abs/{arxiv}'))
    if item.get('pdf'):
        links.append(compact_link('PDF', item['pdf']))
    if item.get('url'):
        links.append(compact_link('Publication', item['url']))
    return '<span class="publication-links">' + '<span class="link-dot" aria-hidden="true">·</span>'.join(s for s in links if s) + '</span>' if any(links) else ''


def bibtex(item: dict) -> str:
    if item.get('bibtex'):
        return str(item['bibtex']).strip()
    authors = item.get('authors') or []
    author_names = []
    for a in authors:
        parts = str(a).split()
        author_names.append((f'{parts[-1]}, {" ".join(parts[:-1])}' if len(parts) > 1 else a))
    key = re.sub(r'[^a-z0-9]', '', (authors[0].split()[-1] if authors else 'author').lower())
    key += str(item.get('year') or '')
    key += re.sub(r'[^a-zA-Z0-9]', '', str(item.get('title', '')).split()[0]).lower()
    entrytype = 'article' if item.get('type') == 'journal' else 'inproceedings' if item.get('type') == 'conference' else 'misc'
    fields = [f'title = {{{item.get("title", "")}}}', f'author = {{{" and ".join(author_names)}}}', f'year = {{{item.get("year", "")}}}']
    venue = item.get('proceedings') or item.get('venue')
    if venue:
        fields.append(f'{"journal" if entrytype == "article" else "booktitle" if entrytype == "inproceedings" else "howpublished"} = {{{venue}}}')
    if item.get('pages'):
        fields.append(f'pages = {{{str(item["pages"]).replace("–", "--")}}}')
    if item.get('doi'):
        fields.append(f'doi = {{{str(item["doi"]).replace("https://doi.org/", "")}}}')
    return '@' + entrytype + '{' + key + ',\n  ' + ',\n  '.join(fields) + '\n}'


def pub_entry(item: dict) -> str:
    slug = re.sub(r'[^a-z0-9-]', '-', item['_slug'].lower())
    target = 'pub-' + slug
    title = e(item.get('title', 'Untitled'))
    authors = item.get('authors') or []
    authors_html = ', '.join(f'<strong>{e(a)}</strong>' if a == 'Aidin Attar' else e(a) for a in authors)
    where = item.get('venue', '')
    year = item.get('year', '')
    summary = ' · '.join(e(x) for x in [where, year] if x)
    detail_pairs = [('Type', {'conference':'Conference paper','journal':'Journal article','preprint':'Preprint','book':'Book chapter'}.get(item.get('type'), 'Publication')),
                    ('Venue', where), ('Proceedings', item.get('proceedings')),
                    ('Year', year), ('Pages', item.get('pages')),
                    ('DOI', item.get('doi'))]
    details = ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k,v in detail_pairs if v)
    abstract = f'<section class="publication-dialog__section"><h3>Abstract</h3><p>{e(item["abstract"])}</p></section>' if item.get('abstract') else ''
    citations = e(bibtex(item))
    links = pub_links(item)
    return f'''<article class="publication-entry" aria-labelledby="{target}-title">
  <div class="publication-entry__body">
    <h3 id="{target}-title"><button class="publication-entry__open" type="button" data-dialog="{target}" aria-haspopup="dialog">{title}<span aria-hidden="true" class="publication-entry__arrow">↗</span></button></h3>
    <p class="publication-entry__authors">{authors_html}</p>
    <p class="publication-entry__venue">{summary}</p>
    <div class="publication-entry__actions">{links}<button class="publication-details-link" type="button" data-dialog="{target}" aria-haspopup="dialog">Details <span aria-hidden="true">↗</span></button></div>
  </div>
</article>
<dialog class="publication-dialog" id="{target}" aria-labelledby="{target}-modal-title">
  <div class="publication-dialog__content">
    <form method="dialog"><button class="publication-dialog__close" type="submit" aria-label="Close publication details">×</button></form>
    <p class="eyebrow">Publication details</p>
    <h2 id="{target}-modal-title">{title}</h2>
    <p class="publication-dialog__authors">{authors_html}</p>
    {abstract}
    <section class="publication-dialog__section"><h3>Bibliographic information</h3><dl class="publication-dialog__facts">{details}</dl></section>
    <div class="publication-dialog__links">{links}</div>
    <section class="publication-dialog__section publication-citation"><div class="publication-citation__heading"><h3>BibTeX</h3><button class="publication-citation__copy" type="button" data-copy-bibtex>Copy BibTeX</button></div><pre><code>{citations}</code></pre></section>
  </div>
</dialog>'''


published = [item for item in items('publications') if item.get('published', True)]
published.sort(key=lambda p: (-int(p.get('year') or 0), str(p.get('title','')).lower()))
by_type = [('journal', 'Journal articles'), ('conference', 'Conference papers'), ('preprint', 'Preprints'), ('book', 'Book chapters')]
publication_parts = ['<div class="publications-list">']
for typ, label in by_type:
    entries = [p for p in published if p.get('type') == typ]
    if entries:
        publication_parts.append(f'<section class="publication-section" aria-label="{e(label)}"><h2>{e(label)}</h2>')
        publication_parts.extend(pub_entry(item) for item in entries)
        publication_parts.append('</section>')
other_entries = [p for p in published if p.get('type') not in dict(by_type)]
if other_entries:
    publication_parts.append('<section class="publication-section"><h2>Other publications</h2>')
    publication_parts.extend(pub_entry(item) for item in other_entries)
    publication_parts.append('</section>')
if not published:
    publication_parts.append('<p class="muted-empty">No publications listed yet.</p>')
publication_parts.append('</div>')
write('publications.html', '\n'.join(publication_parts))

theses = sorted(items('theses'), key=lambda item: int(item.get('order') or 9999))
thesis_html = []
for t in theses:
    label = ' · '.join(e(s) for s in [t.get('degree'), t.get('institution'), t.get('year')] if s)
    title = e(t.get('title', ''))
    href = url(t.get('url'))
    action = f'<a href="{href}" target="_blank" rel="noopener noreferrer">Read thesis <span aria-hidden="true">↗</span></a>' if href else ''
    desc = f'<p class="thesis-entry__description">{e(t["description"])}</p>' if t.get('description') else ''
    thesis_html.append(f'<article class="thesis-entry"><p class="thesis-entry__meta">{label}</p><h3>{title}</h3>{desc}<div class="thesis-entry__link">{action}</div></article>')
write('theses.html','\n'.join(thesis_html))

projects = items('projects')
projects.sort(key=lambda p: (int(p.get('order') or 9999), p.get('title','')))

def project_card(item: dict, featured: bool = False) -> str:
    cls = 'featured-card' if featured else 'compact-card'
    picture = ''
    if featured and url(item.get('image')):
        contain = ' card-image--contain' if item.get('image_contain') else ''
        picture = f'<div class="card-image{contain}"><img src="{url(item["image"])}" alt="{e(item.get("image_alt", ""))}" loading="lazy"></div>'
    details = f'<p>{e(item["details"])}</p>' if item.get('details') else ''
    repo = compact_link('View repository', item.get('repository')) if item.get('repository') else ''
    return f'<article class="card {cls}">{picture}<span class="card-meta">{e(item.get("category", ""))}</span><h3>{e(item.get("title", ""))}</h3><p>{e(item.get("summary", ""))}</p>{details}<p>{repo}</p></article>'

write('projects-featured.html','<div class="card-grid featured-grid">\n'+ '\n'.join(project_card(p,True) for p in projects if p.get('featured'))+'\n</div>')
write('projects-additional.html','<div class="card-grid compact-grid">\n'+ '\n'.join(project_card(p,False) for p in projects if not p.get('featured'))+'\n</div>')
write('home-projects.html','<div class="card-grid">\n'+ '\n'.join(project_card({**p,'details':''},False) for p in projects if p.get('home'))+'\n</div>')

# Pages CMS writes TOML literal strings with single quotes, while Franklin's
# +++ page variables must be valid Julia expressions. Normalize in the build
# workspace before Franklin reads notes, without changing any note body.
normalize_all()
note_entries = []
unpublished_notes = []
for source in sorted(NOTES.glob('*.md')):
    content = source.read_text(encoding='utf-8')
    match = re.match(r'\A\+\+\+\s*\n(.*?)\n\+\+\+\s*\n', content, re.S)
    if not match:
        raise ValueError(f'{source}: expected +++ TOML/Franklin frontmatter')
    meta = tomllib.loads(match.group(1))
    # Explicitly guard against TOML-only types (for instance unquoted dates),
    # which Franklin's Julia-based +++ header cannot interpret as intended.
    from datetime import date, datetime, time
    if any(isinstance(v, (date, datetime, time, dict)) for v in meta.values()):
        raise ValueError(f'{source}: frontmatter must use Julia-compatible scalar, string, or array values; quote dates')
    if not meta.get('published', True):
        unpublished_notes.append(f'notes/{source.name}')
        continue
    meta['_slug'] = source.stem
    note_entries.append(meta)
# Keep unpublished notes out of Franklin's routing, not just the index.
# config.md reads this file to extend its ignore list during a build.
write('unpublished-notes.txt', '\n'.join(unpublished_notes))
note_entries.sort(key=lambda m: (int(m.get('order') or 9999), str(m.get('title') or '')))
notes_markup = []
for n in note_entries:
    href = '/notes/' + n['_slug'] + '/'
    img = url(n.get('image'))
    alt = e(n.get('image_alt', ''))
    typ = 'note-preview-image--plot' if n.get('category') == 'Research note' else 'note-preview-image--photo'
    media = f'<a class="note-preview-link note-preview-media" href="{e(href)}" aria-label="Read {e(n.get("title", ""))}"><div class="card-image note-preview-image {typ}"><img src="{img}" alt="{alt}" loading="lazy"></div></a>' if img else ''
    tags = ' · '.join(e(tag) for tag in n.get('topics', []))
    notes_markup.append(f'''<article class="card featured-card note-preview-card">{media}<div class="note-preview-body">
      <p class="card-meta">{e(n.get('category', 'Note'))}</p>
      <h3><a href="{e(href)}">{e(n.get('title',''))}</a></h3>
      <p>{e(n.get('summary') or n.get('description', ''))}</p>
      <p class="note-preview-topics">{tags}</p>
      <p class="note-preview-action"><a href="{e(href)}">Read note</a></p>
    </div></article>''')
write('notes.html','<div class="card-grid note-preview-grid">\n' + '\n'.join(notes_markup) + '\n</div>' if notes_markup else '<p>No notes published yet.</p>')
print(f'Generated {len(published)} publications, {len(theses)} theses, {len(projects)} projects, {len(note_entries)} notes.')
