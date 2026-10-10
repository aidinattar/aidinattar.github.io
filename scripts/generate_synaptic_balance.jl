#!/usr/bin/env julia
# Execute the figure code shown in the published note instead of maintaining
# a second, potentially diverging copy of the numerical experiment.

const ROOT = normpath(joinpath(@__DIR__, ".."))
const SLUG = "synaptic-balance-from-local-rescaling-to-global-order"
const NOTE = joinpath(ROOT, "notes", SLUG * ".md")
const ASSET_DIR = joinpath(ROOT, "_assets")
const SVG = SLUG * ".svg"

function extract_figure_source(markdown::String)
    # An ordinary fenced Julia block is for display; this standalone script
    # deliberately evaluates the same block to generate the static SVG.
    matches = collect(eachmatch(r"(?ms)^```julia[ \t]*\r?\n(.*?)^```[ \t]*$", markdown))
    candidates = [m.captures[1] for m in matches if occursin("using CairoMakie", m.captures[1]) && occursin("run_balancing", m.captures[1])]
    length(candidates) == 1 || error("Expected exactly one CairoMakie balancing code block in $(NOTE); found $(length(candidates)).")
    source = only(candidates)
    expected_save = "save(\"$(SVG)\", fig)"
    occursin(expected_save, source) || error("Update the save() call in the Markdown to: $(expected_save)")
    return source
end

function main()
    isfile(NOTE) || error("Missing note: $(NOTE)")
    source = extract_figure_source(read(NOTE, String))
    mkpath(ASSET_DIR)
    target = joinpath(ASSET_DIR, SVG)
    # Running from the asset directory makes the save() line in the displayed
    # example reproducible without Franklin's @OUTPUT macro.
    cd(ASSET_DIR) do
        Base.include_string(Main, source, NOTE * " (figure code)")
    end
    isfile(target) && filesize(target) > 0 || error("Figure was not generated: $(target)")
    startswith(strip(read(target, String)), "<?xml") || occursin("<svg", read(target, String)) || error("Unexpected SVG contents: $(target)")
    println("Generated $(relpath(target, ROOT))")
end

main()
