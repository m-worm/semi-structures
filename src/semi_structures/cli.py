"""Command-line interface: the same operations the MCP server exposes.

Both front-ends are thin wrappers over :mod:`semi_structures.mcp_tools`, so a
shell script, a Makefile and an LLM client drive identical code and get
identical answers. Everything reads and writes JSON process documents:

    semi-structures materials --family "Group IV"
    semi-structures examples
    semi-structures example damascene > cell.json
    semi-structures validate cell.json
    semi-structures inspect cell.json
    semi-structures render cell.json --out trench.png --view section
    semi-structures export cell.json > build_cell.py

``-`` means standard input, so documents can be piped:

    semi-structures example damascene | semi-structures render - --out t.png

Unlike the MCP server, the CLI is trusted: ``render --out`` writes wherever
the caller can write, because a shell user already has that power. Pass
``--sandbox`` to apply the server's output-directory confinement instead.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__, mcp_tools
from .mcp_tools import ToolError


def _read_document(source):
    """Load a process document from a path, or from stdin when given ``-``."""
    try:
        text = sys.stdin.read() if source == "-" else open(
            source, encoding="utf-8").read()
    except OSError as error:
        raise ToolError(f"cannot read {source}: {error}") from error
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ToolError(f"{source}: invalid JSON -- {error}") from error


def _emit(value, *, compact=False):
    json.dump(value, sys.stdout, indent=None if compact else 2)
    sys.stdout.write("\n")


def _cmd_materials(args):
    if args.name:
        return _emit(mcp_tools.get_material(args.name), compact=args.compact)
    result = mcp_tools.list_materials()
    if args.family:
        needle = args.family.lower()
        result["materials"] = [m for m in result["materials"]
                               if needle in m["family"].lower()]
        result["count"] = len(result["materials"])
    if args.table:
        rows = [("material", "hex", "rho_e", "alpha", "family")]
        rows += [(m["label"], m["hex"],
                  "-" if m["electron_density"] is None
                  else f"{m['electron_density']:.2f}",
                  f"{m['alpha']:.2f}", m["family"].split(" -")[0])
                 for m in result["materials"]]
        widths = [max(len(str(row[i])) for row in rows)
                  for i in range(len(rows[0]))]
        for index, row in enumerate(rows):
            print("  ".join(str(cell).ljust(width)
                            for cell, width in zip(row, widths)).rstrip())
            if index == 0:
                print("  ".join("-" * width for width in widths))
        return None
    return _emit(result, compact=args.compact)


def _cmd_examples(args):
    result = mcp_tools.list_examples()
    if args.table:
        for item in result["examples"]:
            print(f"{item['name']:<18} {item['title']}")
        return None
    return _emit(result, compact=args.compact)


def _cmd_example(args):
    item = mcp_tools.get_example(args.name)
    return _emit(item["document"] if args.document_only else item,
                 compact=args.compact)


def _cmd_validate(args):
    report = mcp_tools.validate_process(_read_document(args.document))
    if not args.quiet:
        _emit(report, compact=args.compact)
    return 0 if report["valid"] else 1


def _cmd_inspect(args):
    return _emit(mcp_tools.inspect_structure(_read_document(args.document)),
                 compact=args.compact)


def _cmd_render(args):
    document = _read_document(args.document)
    labels = False if args.no_labels else (
        args.labels.split(",") if args.labels else "all")
    options = dict(backend=args.backend, view=args.view, labels=labels,
                   print_width_in=args.width, dpi=args.dpi, y=args.y,
                   azimuth=args.azimuth, elevation=args.elevation,
                   zoom=args.zoom)
    if args.sandbox:
        result = mcp_tools.render_structure(document, args.out, **options)
    else:
        # Trusted path: render straight to the caller's chosen location.
        result = mcp_tools.render_to_path(document, args.out, **options)
    if not args.quiet:
        _emit(result, compact=args.compact)
    return None


def _cmd_export(args):
    result = mcp_tools.export_python(_read_document(args.document),
                                     variable=args.variable)
    sys.stdout.write(result["source"])
    return None


def _cmd_serve(args):
    from .mcp_server import main as serve

    return serve(transport=args.transport)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="semi-structures",
        description="Material-aware semiconductor structure figures: inspect "
                    "the palette, validate and render process documents, and "
                    "export them as package scripts.",
        epilog="A document is JSON (see 'semi-structures example damascene'). "
               "Use '-' to read one from standard input.")
    parser.add_argument("--version", action="version",
                        version=f"semi-structures {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--compact", action="store_true",
                        help="emit JSON on one line")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("materials", parents=[common],
                       help="list the palette, or describe one material")
    p.add_argument("name", nargs="?", help="a material name, e.g. SiO2")
    p.add_argument("--family", help="filter by family substring")
    p.add_argument("--table", action="store_true",
                   help="human-readable table instead of JSON")
    p.set_defaults(func=_cmd_materials)

    p = sub.add_parser("examples", parents=[common],
                       help="list the built-in process-language patterns")
    p.add_argument("--table", action="store_true")
    p.set_defaults(func=_cmd_examples)

    p = sub.add_parser("example", parents=[common],
                       help="print one pattern's process document")
    p.add_argument("name")
    p.add_argument("--full", dest="document_only", action="store_false",
                   help="include the title and summary, not just the document")
    p.set_defaults(func=_cmd_example, document_only=True)

    p = sub.add_parser("validate", parents=[common],
                       help="check a document; exit 1 if it is invalid")
    p.add_argument("document")
    p.add_argument("--quiet", action="store_true",
                   help="report only through the exit status")
    p.set_defaults(func=_cmd_validate)

    p = sub.add_parser("inspect", parents=[common],
                       help="bounds, features, history and chosen renderer")
    p.add_argument("document")
    p.set_defaults(func=_cmd_inspect)

    p = sub.add_parser("render", parents=[common], help="draw a document")
    p.add_argument("document")
    p.add_argument("--out", "-o", required=True,
                   help="output file (.png, .pdf or .svg)")
    p.add_argument("--backend", default="auto",
                   choices=["auto", "vector", "solid"])
    p.add_argument("--view", default="3d", choices=["3d", "section"])
    p.add_argument("--labels", help="comma-separated feature names")
    p.add_argument("--no-labels", action="store_true")
    p.add_argument("--width", type=float, default=6.3,
                   metavar="INCHES", help="print width (default 6.3)")
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--y", type=float, help="section plane (with --view section)")
    p.add_argument("--azimuth", type=float)
    p.add_argument("--elevation", type=float)
    p.add_argument("--zoom", type=float)
    p.add_argument("--sandbox", action="store_true",
                   help="confine the output to the MCP server's directory")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=_cmd_render)

    p = sub.add_parser("export", parents=[common],
                       help="emit an editable Python script for a document")
    p.add_argument("document")
    p.add_argument("--variable", default="w", help="wafer variable name")
    p.set_defaults(func=_cmd_export)

    p = sub.add_parser("serve", parents=[common],
                       help="run the MCP server (needs the 'mcp' extra)")
    p.add_argument("--transport", default="stdio",
                   choices=["stdio", "sse", "streamable-http"])
    p.set_defaults(func=_cmd_serve)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args) or 0
    except ToolError as error:
        print(f"semi-structures: {error}", file=sys.stderr)
        return 2
    except BrokenPipeError:                    # e.g. piping into `head`
        return 0


if __name__ == "__main__":
    sys.exit(main())
