"""MCP server exposing the process language to chatbots and coding agents.

The server is deliberately thin. Every operation lives in
:mod:`semi_structures.mcp_tools` as a plain function; this module only binds
those functions to the Model Context Protocol and starts a transport. The
same functions back the command-line interface, so both front-ends behave
identically.

Run it over stdio::

    semi-structures-mcp
    # or: python -m semi_structures.mcp_server
    # or: semi-structures serve

Configure a client (Claude Desktop, an IDE agent) with that command. Set
``SEMI_STRUCTURES_MCP_OUTPUT`` to choose where rendered figures are written;
otherwise a ``semi-structures-mcp`` folder in the system temp directory is
used and created on demand.

What the server will not do, by construction: it never executes caller-
supplied Python or shell, it replays only public ``Wafer`` verbs from a JSON
process document, it writes only into the one output directory, and it bounds
document size, repeat counts and image dimensions. See
:mod:`semi_structures.mcp_tools` for the limits.

Requires the ``mcp`` extra::

    python -m pip install "semi-structures[mcp]"
"""
from __future__ import annotations

from . import __version__, mcp_tools

INSTRUCTIONS = """\
semi-structures draws material-aware semiconductor structure figures from a
JSON process document: an ordered list of fabrication verbs (deposit, etch,
fill, implant, strip, ...) that is replayed to build a model and then
rendered.

Suggested order of use:

1. `list_examples` / `get_example` to see the document format in working form.
2. Build or edit a document, then `validate_process` to check it. The report
   names the renderer that would be selected and warns about anything
   ambiguous.
3. `inspect_structure` for bounds, features and the process history.
4. `render_structure` to draw it. Prefer `backend="auto"`, which picks the
   exact vector engine for rectilinear flows and the Boolean solid model for
   curved or rotated shapes, circular wafers and implants.
5. `export_python` when the user wants an editable script rather than an
   image.

Colour means material, never circuit role: use `list_materials` and pass
material names, not hex. Text sizes are points at print width and nothing may
fall below 7 pt.
"""


def _missing_sdk(error):
    raise SystemExit(
        "the MCP server needs the 'mcp' extra:\n"
        "    python -m pip install \"semi-structures[mcp]\"\n"
        f"(import failed: {error})")


def build_server():
    """Create the server with every tool registered.

    Binds to whichever MCP SDK generation is installed: 2.x exposes
    ``MCPServer``, 1.x exposes ``FastMCP``. Both provide the same ``.tool()``
    decorator and ``.run(transport=...)``.
    """
    try:
        from mcp.server.mcpserver import MCPServer as Server      # SDK 2.x
    except ImportError:
        try:
            from mcp.server.fastmcp import FastMCP as Server      # SDK 1.x
        except ImportError as error:
            _missing_sdk(error)

    server = Server(name="semi-structures", version=__version__,
                    instructions=INSTRUCTIONS)

    # Each tool keeps the docstring and signature of the underlying function,
    # which is what the client sees as the tool's description and schema.
    for function in mcp_tools.TOOLS:
        server.tool()(function)
    return server


def main(transport="stdio"):
    """Entry point for ``semi-structures-mcp``."""
    build_server().run(transport=transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
