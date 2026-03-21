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

## GitHub Pages

The repository includes a GitHub Actions workflow for Pages deployment. After merging into `main`:

1. open repository `Settings > Pages`
2. set `Source` to `GitHub Actions`
3. future pushes to `main` will build Franklin and deploy `__site`

The workflow also copies the Google Search Console verification file into the final site output so it is served as a raw `.html` file at the root.
