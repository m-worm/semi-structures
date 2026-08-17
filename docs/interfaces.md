# Command line and MCP server

Besides the Python API, `semi-structures` ships two front-ends that speak the
same language: a **command-line interface** for shells, Makefiles and CI, and
an **MCP server** for chatbots and coding agents.

Both are thin wrappers over `semi_structures.mcp_tools`, where every operation
is a plain function. There is no second implementation of anything: the CLI and
the server validate, inspect, render and export through identical code, so they
cannot disagree.

```text
                    semi_structures.mcp_tools
                    (validate, inspect, render, export, palette, patterns)
                       |                              |
        semi_structures.cli                semi_structures.mcp_server
        (argparse, JSON in/out)            (Model Context Protocol, stdio)
```

The unit of exchange is a **process document**: JSON describing an ordered list
of fabrication verbs. See [Saving a model as JSON](../README.md#saving-a-model-as-json)
for the format, and `semi_structures.serialize` for the details.

---

## Command-line interface

Installed as `semi-structures` by the package.

```text
semi-structures materials --table            # the palette
semi-structures materials SiO2               # one material, as JSON
semi-structures examples                     # built-in process patterns
semi-structures example damascene            # one pattern's document
semi-structures validate cell.json           # check it; exit 1 if invalid
semi-structures inspect cell.json            # bounds, features, history
semi-structures render cell.json -o fig.png  # draw it
semi-structures export cell.json             # emit an editable script
semi-structures serve                        # run the MCP server
```

Everything reads and writes JSON, and `-` means standard input, so the
commands compose:

```text
semi-structures example memory-holes | semi-structures render - -o holes.png
semi-structures example damascene > cell.json
semi-structures export cell.json > build_cell.py && python build_cell.py
```

### Commands

| Command | What it does |
|---|---|
| `materials [NAME]` | The whole palette, or one material's fill, electron density, drawing alpha and family. `--family SUBSTRING` filters; `--table` prints a human-readable table instead of JSON. |
| `examples` | The built-in process-language patterns. `--table` for a plain list. |
| `example NAME` | One pattern's process document, ready to render. `--full` adds the title and summary. |
| `validate DOCUMENT` | Reports errors, warnings, the renderer that would be chosen, and the normalized document. Exit status 1 if invalid, so it works in a shell test. `--quiet` reports only through the exit status. |
| `inspect DOCUMENT` | Footprint, z extent, feature list, operation history, notch, and counts. |
| `render DOCUMENT -o FILE` | Draws the document. `--view section` for a 2D cross-section (with `--y`), `--backend`, `--labels a,b`, `--no-labels`, `--width`, `--dpi`, and `--azimuth/--elevation/--zoom` for the solid camera. |
| `export DOCUMENT` | Prints an editable Python script that rebuilds the model. |
| `serve` | Runs the MCP server (`--transport stdio`, `sse` or `streamable-http`). |

Exit status is `0` on success, `1` for an invalid document under `validate`,
and `2` for a refused request (bad filename, unreadable file, malformed JSON).

The CLI is **trusted**: `render -o` writes wherever you can write, because a
shell user already has that power. Pass `--sandbox` to apply the server's
output-directory confinement instead.

---

## MCP server

Installed as `semi-structures-mcp`. Requires the `mcp` extra:

```text
python -m pip install "semi-structures[mcp]"
```

Run it directly, or through the CLI:

```text
semi-structures-mcp
semi-structures serve
python -m semi_structures.mcp_server
```

### Configuring a client

Point any MCP client at the command. For Claude Desktop, in
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "semi-structures": {
      "command": "semi-structures-mcp",
      "env": {
        "SEMI_STRUCTURES_MCP_OUTPUT": "/path/to/figures"
      }
    }
  }
}
```

`SEMI_STRUCTURES_MCP_OUTPUT` is the one directory the server may write to. If
unset, a `semi-structures-mcp` folder in the system temp directory is created
and used.

The server works with both generations of the Python SDK: it binds to
`MCPServer` (SDK 2.x) or `FastMCP` (SDK 1.x), whichever is installed.

### Tools

| Tool | Purpose | Writes |
|---|---|---|
| `list_materials` | The palette: fill, electron density, drawing alpha, family. | no |
| `get_material` | One material, with a spelling hint if the name is close. | no |
| `list_examples` | The built-in process-language patterns. | no |
| `get_example` | One pattern, with a normalized, ready-to-render document. | no |
| `validate_process` | Errors, warnings, chosen renderer, normalized document. Never raises for a bad document -- the report is the answer. | no |
| `inspect_structure` | Footprint, z extent, features, counts, history, notch. | no |
| `render_structure` | Draws a document into the output directory. | yes |
| `export_python` | Returns an editable package script for a document. | no |

The server also sends instructions telling the model the intended order of
use: read a pattern, build a document, validate, inspect, then render.

### What the server will not do

These are enforced in `mcp_tools`, not in the transport, so the CLI inherits
the same guarantees where they apply:

- **No code execution.** A request is a process document, never Python. Only
  methods marked as DSL verbs may be replayed. The check is an allowlist, so
  a document cannot reach some other public method that happens to exist.
- **One writable directory.** A filename must be a bare name, with no
  separator, no `..` and no surprising suffix, and the resolved path is
  re-checked against
  the output directory before anything is written.
- **Bounded work.** At most 500 operations per document, 2000 repeats in one
  `add_multilayer`, and a 40-megapixel ceiling on any rendered image.
- **No silent approximation.** A forced `vector` backend request for geometry
  the vector engine cannot draw exactly is refused rather than approximated.

### Worked exchange

```text
get_example {"name": "damascene"}
  -> a five-operation document: oxide, hard mask, trench, Cu fill, strip

validate_process {"document": {...}}
  -> {"valid": true, "backend": "vector", "warnings": [], "normalized": {...}}

render_structure {"document": {...}, "filename": "trench.png",
                  "view": "section"}
  -> {"path": ".../trench.png", "bytes": 7068, "backend": "vector"}

export_python {"document": {...}}
  -> a runnable script using Wafer, Rectangle, ...
```

---

## Which to use

| Situation | Use |
|---|---|
| Writing a figure by hand, with full control | the Python API |
| Scripting, Makefiles, CI, batch regeneration | the CLI |
| A chatbot or coding agent authoring figures | the MCP server |
| Anything the DSL cannot express yet | the Python API, plus `Scene` directly |
