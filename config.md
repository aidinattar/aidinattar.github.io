+++
author = "Aidin Attar"
mintoclevel = 2

ignore = [
  "node_modules/",
  "content/",
  "scripts/",
  "Project.toml",
  "Manifest.toml",
  ".gitignore",
  "google4083dfcedcc5d554.html",
]

# build_content.py writes an ignore list for unpublished notes. Note files remain
# under notes/ because Franklin and Pages CMS both read them directly.
if isfile("_layout/generated/unpublished-notes.txt")
  for path in eachline("_layout/generated/unpublished-notes.txt")
    isempty(path) || push!(ignore, path)
  end
end

generate_rss = false
website_title = "Aidin Attar"
website_descr = "Research website of Aidin Attar, PhD student in Information Engineering at the University of Padova."
website_url = "https://aidinattar.github.io/"
+++
