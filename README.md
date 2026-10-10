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
| Notes | `content/notes/*.md` (TOML frontmatter + Franklin Markdown) | Notes index and individual `/notes/<filename>/` pages |

**Do not edit** `_layout/generated/*` or `notes/*.md` directly: these files are generated before deployment. Edit the matching source under `content/` instead. Page copy outside the four collections (home, research, CV, contact) remains in the original Markdown files and can still be edited normally in GitHub.

Notes use the Pages CMS **code editor** for the body, intentionally rather than WYSIWYG, to preserve Franklin math (`$$...$$`), LaTeX expressions, HTML sections, Julia code blocks, and citations. For a new note, start the body with a heading (`# My note`) or a custom HTML intro. Preview images belong in `_assets` and are referenced as `/assets/...`.

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

Projects can be marked `featured` (large card in Projects) and `home` (shown on the homepage). Notes are ordered by `order` and can be hidden with `published: false`. The `order` field also controls the project and thesis ordering.
