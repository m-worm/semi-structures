# Contributing

Issues and pull requests are welcome. This file covers the house rules, how to
run everything, and what "done" means for a new capability.

## Setup

```text
git clone https://github.com/m-worm/semi-structures.git
cd semi-structures
python -m pip install -e ".[solid,dev,mcp]"
```

The core package needs only NumPy and Matplotlib. `solid` adds the Boolean
backend (PyVista, trimesh, manifold3d, Pillow), `dev` adds pytest and build,
and `mcp` adds the MCP SDK. Tests for a missing extra skip rather than fail.

## Verify

```text
python -m pytest              # the whole suite
python examples/run_all.py    # every figure, into docs/figures/
python -m build               # sdist and wheel
```

Rebuild the showcase after regenerating figures:

```text
cd docs && pdflatex showcase.tex && pdflatex showcase.tex
```

CI runs the suite on Linux and Windows for Python 3.10 to 3.12, exercises the
command-line entry points, regenerates every figure, and builds the
distribution.

## House rules

These are what keep figures consistent across a document written over months.

1. **Colour means material, never circuit role.** Fills come from
   `style.MATERIAL`. Hue is the chemical family and lightness tracks electron
   density. Raw hex is allowed, but only as a deliberate presentation override
   in a separate, clearly labeled script, never to imitate a material.
2. **Nothing below 7 pt.** Every text size is points at print width, in every
   renderer. The backends refuse smaller sizes rather than shrink text. If a
   face is too small to carry a label, use a leader.
3. **Author through the process DSL.** Device structures should be built from
   fabrication verbs, and `backend="auto"` then picks the cheapest renderer
   that preserves the geometry. Use `Box`, `Pillar` or `Scene` directly for
   package assemblies, annotations and renderer tests, not to fake an etch or
   an implant by overlapping independent solids.
4. **Saturated colors are reserved** for beams and fields. Annotation text is
   slate, and leaders are thin gray.
5. **Documentation examples must run.** Every ```` ```python ```` block in a
   markdown file is executed by `tests/test_docs.py`. Blocks in one file share
   a namespace and run in order, so a later block may continue an earlier one.
   Anything deliberately not runnable, such as a proposed API or a shell
transcript,
   goes in a ```` ```text ```` block instead.

## Definition of done

A new capability is finished when all of these hold:

- it is reachable from the process DSL, or there is a written reason it cannot
  be,
- automatic backend selection still picks a renderer that preserves it, and a
  forced backend that cannot draw it raises rather than approximating,
- a test covers it, and an example figure exercises it if it is visual,
- it survives a JSON round-trip (`to_json` → `from_json` → same model), which
  is asserted for the whole DSL in `tests/test_serialize.py`,
- any documentation snippet showing it runs, which `tests/test_docs.py`
  checks,
- the capability table in [`ROADMAP.md`](ROADMAP.md) is updated in the same
  change, along with any affected documentation,
- `python -m pytest` and `python examples/run_all.py` are clean.

## Adding an example figure

1. Write `examples/fig_<name>.py` with a module docstring saying what it shows
   and which outputs it writes into `docs/figures/`.
2. Register it in `examples/run_all.py` and in the table in
   `examples/README.md`.
3. Add the prompt that would produce it to `docs/prompt-gallery.md`.
4. If it came from a reference image, record the provenance in
   `examples/REFERENCES.md`. Use a supplied image for composition, viewpoint
   and callouts only. Write new geometry, and never redistribute the image.
5. Add a figure and caption to `docs/showcase.tex`, naming the generating
   script.
6. Inspect the rendered PNG and fix any collisions before committing.

## Documentation layout

| File | Holds |
|---|---|
| `README.md` | What the package is, install, quick start, the tour |
| `docs/guide.md` | The manual: DSL, renderers, solid API, palette reference |
| `docs/interfaces.md` | The command line and the MCP server |
| `docs/prompt-gallery.md` | Prompts and the figures they produce |
| `docs/structure3d-skill.md` | The rule sheet a coding assistant follows |
| `examples/README.md` | Every generator and the feature it covers |
| `examples/REFERENCES.md` | Literature and reference-image provenance |
| `ROADMAP.md` | Release checklist, capability status, design targets |
| `CONTRIBUTING.md` | House rules, verification, definition of done |
| `CHANGELOG.md` | Release history |

When these disagree, the public API and the tests win. Correct the affected
documents in the same change.
