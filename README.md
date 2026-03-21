# aidinattar.github.io

Personal website of Aidin Attar, rebuilt in Franklin.jl with a research-first structure.

## Local development

Install dependencies:

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

Run the local server:

```bash
julia --project=. -e 'using Franklin; serve()'
```

Generate the production site:

```bash
julia --project=. -e 'using Franklin; optimize()'
```

## Notes

The active source for the site lives in the markdown pages together with the `_layout`, `_css`, and `_assets` directories at the repository root.
