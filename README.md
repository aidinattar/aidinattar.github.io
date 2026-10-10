# Personal research website

Personal site built with [Franklin.jl](https://franklinjl.org/) and published through GitHub Pages. Academic content is maintained with [Pages CMS](https://pagescms.org/).

## Editing with Pages CMS

1. Go to **https://pagescms.org/** and sign in with GitHub.
2. Choose the repository **`aidinattar/aidinattar.github.io`**, branch **`main`** (grant repository access if asked).
3. Edit **Publications**, **Theses**, **Projects**, or **Notes**. Each record is its own file; you can create new records without changing the HTML.
4. Save. Pages CMS commits the change to GitHub; the existing GitHub Actions workflow builds and deploys the site automatically.

The first-time connection to Pages CMS/GitHub is an account authorization, not an additional deployment secret.

## Source of truth

| CMS collection | Source files | Website display |
|---|---|---|
| Publications | `content/publications/*.json` | Compact bibliography, modal details, auto-BibTeX |
| Theses | `content/theses/*.json` | Theses section of Publications |
| Projects | `content/projects/*.json` | Projects page and selected homepage projects |
| Notes | `notes/*.md` (TOML-compatible Franklin +++ frontmatter) | Notes index and individual `/notes/<filename>/` pages |

**Do not edit** `_layout/generated/*` directly: these HTML lists are generated before deployment. Notes live only in `notes/*.md` and are edited directly through Pages CMS or in Git. The other collections have sources under `content/`. Page copy outside the four collections (home, research, CV, contact) remains in the original Markdown files and can still be edited normally in GitHub.

Note formulas are rendered client-side by the locally bundled KaTeX scripts, included only on pages where Franklin detects mathematics. The required scripts are listed in `_layout/foot.html` and `_assets/js/math.js`. Keep these files when changing the site layout.

Notes use the Pages CMS **code editor** for the body, intentionally rather than WYSIWYG, to preserve Franklin math (`$$...$$`), LaTeX expressions, HTML sections, Julia code blocks, and citations. For a new note, start the body with a heading (`# My note`) or a custom HTML intro. Preview images belong in `_assets` and are referenced as `/assets/...`.

### Notes: one directory

The files in `notes/` are the **single source of truth**. Both Pages CMS and Franklin use their `+++` metadata directly; `scripts/build_content.py` only generates the notes listing and an ignore list for unpublished notes. There is no `content/notes/` directory anymore. Keep date values quoted as strings in metadata (e.g. `date = "2026-10-10"`), because Franklin interprets `+++` as Julia code.

### Local development

```bash
python3 scripts/build_content.py
julia --project=. -e 'using Pkg; Pkg.instantiate()'
julia --project=. -e 'using Franklin; serve()'
```

For a static build instead of a dev server:

```bash
python3 scripts/build_content.py
julia --project=. -e 'using Franklin; optimize(clear=true)'
```

Only Python 3.11+ (standard library) and the existing Julia dependencies are needed. The GitHub workflow runs the generator before Franklin so the CMS changes propagate to every relevant page; no extra backend or CMS build service is required.

## Publication fields

Use one JSON record per publication. `title`, `authors` (ordered list), `type`, and `year` control the reference list; `venue`, `proceedings`, `pages`, `abstract`, and the DOI/arXiv/PDF links populate the popup. Provide `bibtex` to override the automatically generated minimal BibTeX. Set `published: false` to hide a work without deleting it.

Projects can be marked `featured` (large card in Projects) and `home` (shown on the homepage). Notes are ordered by `order`. Notes with `published: false` are excluded from the index and Franklin routing at build time (via a generated ignore list). The `order` field also controls the project and thesis ordering.

### Notes created with Pages CMS

Pages CMS saves `notes/*.md` with TOML `+++` frontmatter. Franklin interprets
those fields as Julia expressions, so its parser cannot read TOML's
single-quoted strings. `python3 scripts/build_content.py` automatically
normalizes the metadata into compatible double-quoted Julia/TOML strings before
Franklin builds the site. The Markdown body, mathematics and code are left alone.
The normalization changes files in the working tree; commit those normalized
changes if you want the repository itself to use the canonical format. Pages CMS
may use single quotes again during the next edit, but the build repairs them.

CMS uploads are saved in `_assets/` and served from `/assets/`. Use exactly the
path shown in the CMS media field when inserting images inside a note. The
normalizer checks both cover and inline images for missing local files. If a
missing image in the body has the same filename as a valid cover image, you can
repair it locally with:

```bash
python3 scripts/normalize_notes.py --repair-image-paths
python3 scripts/build_content.py
```

GitHub Actions also checks after Franklin builds that each published note has a
corresponding HTML page before allowing deployment.
