"""Typed operations behind the MCP server, with no MCP dependency.

Every tool the server exposes is a plain function here that takes and returns
JSON-ready values. Keeping this layer free of the SDK means the behaviour can
be tested without installing ``mcp``, and the same functions work whichever
SDK generation :mod:`semi_structures.mcp_server` binds to.

The safety rules the server promises are enforced here, not in the transport:

* no arbitrary code is executed -- a request is a process document (see
  :mod:`semi_structures.serialize`), replayed through the public DSL, and a
  verb that is not a public ``Wafer`` method is refused;
* writes are confined to one output directory (``SEMI_STRUCTURES_MCP_OUTPUT``,
  otherwise a ``semi-structures-mcp`` folder in the system temp directory),
  and a filename may not contain a path separator, a parent reference or an
  unexpected suffix;
* documents, images and repeat counts are bounded, so a malformed or hostile
  request cannot exhaust memory or disk.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from .process import Wafer
from .serialize import FORMAT, VERSION
from .style import FAMILIES, MATERIAL, PRETTY, alpha_for

# -- limits -------------------------------------------------------------------

MAX_OPERATIONS = 500          # operations in one document
MAX_REPEATS = 2_000           # repeats in a single add_multilayer
MAX_PIXELS = 40_000_000       # rendered image area
MAX_PRINT_WIDTH_IN = 20.0
MAX_DPI = 1_200
ALLOWED_SUFFIXES = {".png", ".pdf", ".svg"}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class ToolError(ValueError):
    """A request that the server refuses, with a message meant for the caller."""


# -- output sandbox -----------------------------------------------------------

def output_directory():
    """The one directory the server may write to."""
    configured = os.environ.get("SEMI_STRUCTURES_MCP_OUTPUT")
    directory = (Path(configured) if configured
                 else Path(tempfile.gettempdir()) / "semi-structures-mcp")
    directory.mkdir(parents=True, exist_ok=True)
    return directory.resolve()


def resolve_output_path(filename):
    """Validate ``filename`` and place it inside :func:`output_directory`."""
    if not isinstance(filename, str) or not filename:
        raise ToolError("filename must be a non-empty string")
    if any(sep in filename for sep in ("/", "\\")) or ".." in filename:
        raise ToolError(
            "filename must be a bare name, without a path separator or '..'")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ToolError(
            f"unsupported output type {suffix or '(none)'}; allowed: "
            + ", ".join(sorted(ALLOWED_SUFFIXES)))
    if not _SAFE_NAME.match(filename):
        raise ToolError(
            "filename may use letters, digits, dot, dash and underscore only, "
            "and must start with a letter or digit")
    directory = output_directory()
    path = (directory / filename).resolve()
    # belt and braces: even after the checks above, never escape the sandbox
    if path.parent != directory:
        raise ToolError("resolved path escapes the output directory")
    return path


# -- materials ----------------------------------------------------------------

def _family_of(name):
    for title, members in FAMILIES:
        if name in members:
            return title.replace("$-$", "-").replace("$_2$", "2")
    return "derived or alloy"


def _material_entry(name):
    color, density = MATERIAL[name]
    return {"name": name, "label": PRETTY.get(name, name), "hex": color,
            "electron_density": density, "alpha": alpha_for(name),
            "family": _family_of(name)}


def list_materials():
    """Every material in the palette, with its fill, density and family."""
    names = sorted(MATERIAL)
    return {"count": len(names),
            "materials": [_material_entry(name) for name in names],
            "note": ("Colour means material, never circuit role. Hue is the "
                     "chemical family and lightness tracks electron density; "
                     "alpha below 1 marks the transparent crystals. Raw hex "
                     "is accepted anywhere a material name is, but it is a "
                     "deliberate presentation override.")}


def get_material(name):
    """One material's fill, electron density, drawing alpha and family."""
    if name not in MATERIAL:
        close = [key for key in MATERIAL if key.lower() == str(name).lower()]
        hint = f"; did you mean {close[0]!r}?" if close else ""
        raise ToolError(f"unknown material {name!r}{hint}")
    return _material_entry(name)


# -- process-language patterns ------------------------------------------------

def _pattern_library():
    """Small, known-good process documents that show the language's shape."""
    def document(wafer, operations):
        return {"format": FORMAT, "version": VERSION, "wafer": wafer,
                "operations": operations}

    return {
        "damascene": {
            "title": "Damascene trench and fill",
            "summary": ("Oxide and hard mask, a trench etched to the oxide, "
                        "a Cu fill, then the mask stripped. Rectilinear, so "
                        "it renders on the exact vector backend."),
            "document": document(
                {"size": [10.0, 6.0], "thickness": 2.0, "name": "Si wafer"},
                [{"op": "add_layer", "material": "SiO2", "thickness": 1.2,
                  "name": "oxide"},
                 {"op": "add_layer", "material": "Si3N4", "thickness": 0.5,
                  "name": "hard mask"},
                 {"op": "etch",
                  "shape": {"shape": "rectangle", "center": [5.0, 3.0],
                            "size": [4.0, 6.0], "rotation": 0.0},
                  "stop_on": {"$ref": {"op": 0}}, "name": "trench"},
                 {"op": "fill", "hole": {"$ref": {"op": 2}},
                  "material": "Cu", "name": "Cu"},
                 {"op": "strip", "target": "hard mask"}])},
        "tall-stack": {
            "title": "Tall repeated stack with an elided middle",
            "summary": ("A 100-pair oxide/nitride stack drawn as the bottom "
                        "ten and top five pairs with a break between them; "
                        "render() brackets the block automatically."),
            "document": document(
                {"size": [8.0, 5.0], "thickness": 1.0},
                [{"op": "add_multilayer",
                  "layers": [["SiO2", 0.18], ["Si3N4", 0.22]],
                  "repeats": 100, "name": "ON", "show": [10, 5],
                  "unit": "pairs"}])},
        "notched-wafer": {
            "title": "Circular wafer with a V-notch",
            "summary": ("A 300 mm wafer with an orientation notch and one "
                        "blanket film; the notch cuts the substrate and every "
                        "film that inherits its footprint. Needs the solid "
                        "backend."),
            "document": document(
                {"size": 300.0, "shape": "circle", "thickness": 12.0,
                 "notch": "V", "name": "300 mm wafer"},
                [{"op": "add_layer", "material": "SiO2", "thickness": 4.0,
                  "name": "oxide"}])},
        "implant-and-mesa": {
            "title": "Implanted region and a mesa etch",
            "summary": ("Material replacement inside a patterned region, plus "
                        "a rectangular mesa formed by etching the field "
                        "around it. The implant selects the solid backend."),
            "document": document(
                {"size": [6.0, 4.0], "substrate": "GaN", "thickness": 1.5},
                [{"op": "add_layer", "material": "AlGaN", "thickness": 0.3,
                  "name": "barrier"},
                 {"op": "implant",
                  "shape": {"shape": "rectangle", "center": [1.5, 2.0],
                            "size": [1.0, 1.2], "rotation": 0.0},
                  "material": "SiP", "depth": 0.5, "name": "n+ contact"},
                 {"op": "mesa",
                  "shape": {"shape": "rectangle", "center": [3.0, 2.0],
                            "size": [4.0, 2.6], "rotation": 0.0},
                  "depth": 0.3, "name": "mesa"}])},
        "memory-holes": {
            "title": "Circular memory holes with a nested fill",
            "summary": ("Two circular etches through a stack and a fill in "
                        "one of them -- the 3D NAND pattern. Curved shapes "
                        "select the solid backend."),
            "document": document(
                {"size": [6.0, 4.0], "thickness": 1.0},
                [{"op": "add_multilayer",
                  "layers": [["SiO2", 0.15], ["W", 0.18]], "repeats": 6,
                  "name": "wordlines"},
                 {"op": "etch",
                  "shape": {"shape": "circle", "center": [2.0, 2.0],
                            "radius": 0.45},
                  "through": True, "name": "hole 1"},
                 {"op": "etch",
                  "shape": {"shape": "circle", "center": [4.0, 2.0],
                            "radius": 0.45},
                  "through": True, "name": "hole 2"},
                 {"op": "fill", "hole": {"$ref": {"op": 1}},
                  "material": "Si", "name": "channel"}])},
    }


def list_examples():
    """The available process-language patterns, without their documents."""
    library = _pattern_library()
    return {"count": len(library),
            "examples": [{"name": key, "title": item["title"],
                          "summary": item["summary"]}
                         for key, item in sorted(library.items())]}


def get_example(name):
    """One pattern, including a ready-to-render process document."""
    library = _pattern_library()
    if name not in library:
        raise ToolError(
            f"unknown example {name!r}; available: "
            + ", ".join(sorted(library)))
    item = library[name]
    # Normalize on the way out: the returned document is then exactly what
    # the package would write for the same model, and a pattern that ever
    # stopped being valid would fail here rather than downstream.
    document = _build(item["document"]).to_dict()
    return {"name": name, "title": item["title"], "summary": item["summary"],
            "document": document}


# -- documents ----------------------------------------------------------------

def _check_document_shape(document):
    """Cheap structural checks before anything is replayed."""
    if not isinstance(document, dict):
        raise ToolError("a process document must be a JSON object")
    operations = document.get("operations", [])
    if not isinstance(operations, list):
        raise ToolError("'operations' must be a list")
    if len(operations) > MAX_OPERATIONS:
        raise ToolError(
            f"document has {len(operations)} operations; the limit is "
            f"{MAX_OPERATIONS}")
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise ToolError(f"operation {index} must be an object")
        repeats = operation.get("repeats")
        if isinstance(repeats, (int, float)) and repeats > MAX_REPEATS:
            raise ToolError(
                f"operation {index} repeats {int(repeats)} times; the limit "
                f"is {MAX_REPEATS}")


def _build(document):
    """Replay a document into a Wafer, turning failures into ToolError."""
    _check_document_shape(document)
    try:
        return Wafer.from_dict(document)
    except ToolError:
        raise
    except Exception as error:                     # noqa: BLE001 - reported
        raise ToolError(f"{type(error).__name__}: {error}") from error


def validate_process(document):
    """Check a document and report what it would draw, without drawing it.

    Never raises for a bad document: the report is the answer.
    """
    try:
        wafer = _build(document)
    except ToolError as error:
        return {"valid": False, "errors": [str(error)], "warnings": [],
                "normalized": None}

    warnings = []
    if not wafer.layers:
        warnings.append("the model has no layers")
    unnamed = sum(1 for feature in wafer.features if not getattr(
        feature, "name", None))
    if unnamed:
        warnings.append(
            f"{unnamed} feature(s) have no name; named features can be "
            "referenced by render(labels=[...]) and by later operations")
    if wafer.requires_solid:
        warnings.append(
            "this model needs the solid backend (curved or rotated shapes, a "
            "circular wafer, or an implant), which requires the 'solid' extra")
    return {"valid": True, "errors": [], "warnings": warnings,
            "backend": wafer.select_backend("auto"),
            "normalized": wafer.to_dict()}


def _feature_entry(feature):
    entry = {"name": getattr(feature, "name", None),
             "kind": getattr(feature, "kind", type(feature).__name__),
             "material": getattr(feature, "material", None)}
    for attribute in ("z0", "z1"):
        value = getattr(feature, attribute, None)
        if value is not None:
            entry[attribute] = float(value)
    return entry


def inspect_structure(document):
    """Bounds, features, process history and the renderer that would be used."""
    wafer = _build(document)
    x0, y0, dx, dy = wafer.substrate.extent
    return {
        "backend": wafer.select_backend("auto"),
        "requires_solid": bool(wafer.requires_solid),
        "footprint": {"x": [float(x0), float(x0 + dx)],
                      "y": [float(y0), float(y0 + dy)]},
        "z": {"bottom": float(wafer.bottom), "surface": float(wafer.top)},
        "counts": {"layers": len(wafer.layers), "etches": len(wafer.etches),
                   "fills": len(wafer.fills), "implants": len(wafer.regions),
                   "breaks": len(wafer.breaks)},
        "features": [_feature_entry(feature) for feature in wafer.features],
        "history": [entry["op"] for entry in wafer.to_dict()["operations"]],
        "notch": wafer.notch,
    }


# -- rendering ----------------------------------------------------------------

def render_structure(document, filename, backend="auto", view="3d",
                     labels="all", print_width_in=6.3, dpi=300, y=None,
                     azimuth=None, elevation=None, zoom=None):
    """Validate and render a process document to an image.

    The arguments are spelled out rather than collected, because this
    signature is the schema an MCP client sees.

    ``document``: a process document (see ``get_example``).
    ``filename``: a bare name ending in .png, .pdf or .svg; the file is
    written into the server's output directory.
    ``backend``: "auto" (recommended), "vector" or "solid".
    ``view``: "3d" for the isometric or solid view, "section" for a 2D
    cross-section at plane ``y``.
    ``labels``: "all", false, or a list of feature names.
    ``print_width_in`` and ``dpi``: the printed width and resolution; all
    text is sized in points at that width.
    ``azimuth``, ``elevation``, ``zoom``: camera controls for the solid
    backend.
    """
    return _render(document, resolve_output_path(filename), backend=backend,
                   view=view, labels=labels, print_width_in=print_width_in,
                   dpi=dpi, y=y, azimuth=azimuth, elevation=elevation,
                   zoom=zoom)


def render_to_path(document, path, **options):
    """Validate and render a document to any path the caller chooses.

    For trusted front-ends (the CLI). The suffix is still checked, so a typo
    cannot ask matplotlib for a format it does not have.
    """
    path = Path(path)
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ToolError(
            f"unsupported output type {path.suffix or '(none)'}; allowed: "
            + ", ".join(sorted(ALLOWED_SUFFIXES)))
    if path.parent and not path.parent.exists():
        raise ToolError(f"no such directory: {path.parent}")
    return _render(document, path, **options)


def _render(document, path, *, backend="auto", view="3d",
            labels="all", print_width_in=6.3, dpi=300, y=None,
            azimuth=None, elevation=None, zoom=None):
    """Shared render implementation.

    ``backend`` is ``auto`` (recommended), ``vector`` or ``solid``; a forced
    vector request for geometry it cannot draw exactly is refused rather than
    silently approximated. ``view="section"`` draws the 2D cross-section at
    plane ``y``.
    """
    print_width_in = float(print_width_in)
    dpi = int(dpi)
    if not 0 < print_width_in <= MAX_PRINT_WIDTH_IN:
        raise ToolError(
            f"print_width_in must be in (0, {MAX_PRINT_WIDTH_IN}]")
    if not 0 < dpi <= MAX_DPI:
        raise ToolError(f"dpi must be in (0, {MAX_DPI}]")
    if (print_width_in * dpi) ** 2 > MAX_PIXELS:
        raise ToolError(
            "the requested width and dpi would exceed the "
            f"{MAX_PIXELS // 1_000_000} megapixel limit")

    wafer = _build(document)
    if labels not in (True, False, "all", None) and not isinstance(
            labels, (list, tuple)):
        raise ToolError("labels must be 'all', false, or a list of names")

    import matplotlib
    matplotlib.use("Agg")

    options = {"backend": backend, "labels": labels or False,
               "print_width_in": print_width_in, "dpi": dpi, "view": view}
    if view == "section":
        if y is not None:
            options["y"] = float(y)
    else:
        for key, value in (("azimuth", azimuth), ("elevation", elevation),
                           ("zoom", zoom)):
            if value is not None:
                options[key] = float(value)
    try:
        wafer.render(path=str(path), **options)
    except ToolError:
        raise
    except Exception as error:                     # noqa: BLE001 - reported
        raise ToolError(f"render failed -- {type(error).__name__}: {error}") \
            from error

    return {"path": str(path), "filename": path.name,
            "bytes": path.stat().st_size,
            "backend": wafer.select_backend(backend),
            "view": view}


# -- export -------------------------------------------------------------------

def _literal(value):
    if isinstance(value, dict) and "shape" in value:
        kind, center = value["shape"], tuple(value["center"])
        if kind == "rectangle":
            rotation = value.get("rotation", 0.0)
            extra = f", {rotation!r}" if rotation else ""
            return f"Rectangle({center!r}, {tuple(value['size'])!r}{extra})"
        if kind == "circle":
            return f"Circle({center!r}, radius={value['radius']!r})"
        if kind == "ellipse":
            rotation = value.get("rotation", 0.0)
            extra = f", {rotation!r}" if rotation else ""
            return f"Ellipse({center!r}, {tuple(value['radii'])!r}{extra})"
    if isinstance(value, list):
        # JSON has only lists, but the DSL reads better with the tuples it was
        # written for: size=(10, 6), show=(10, 5), layers=[("SiO2", 0.18), ...]
        if value and all(isinstance(item, (int, float, str)) for item in value):
            inner = ", ".join(_literal(item) for item in value)
            return f"({inner})" if len(value) != 1 else f"({inner},)"
        return "[" + ", ".join(_literal(item) for item in value) + "]"
    return repr(value)


def export_python(document, *, variable="w"):
    """Turn a document into an editable, runnable package script."""
    wafer = _build(document)                       # validates before emitting
    normalized = wafer.to_dict()

    # Only operations that are referenced later need a variable.
    referenced = set()

    def scan(value):
        if isinstance(value, dict):
            if "$ref" in value:
                referenced.add(value["$ref"]["op"])
            else:
                for item in value.values():
                    scan(item)
        elif isinstance(value, list):
            for item in value:
                scan(item)

    for operation in normalized["operations"]:
        scan(operation)

    def reference(address):
        index, item = address["op"], address.get("item")
        if index < 0:
            return f"{variable}.substrate"
        return f"op{index}" + (f"[{item}]" if item is not None else "")

    def argument(value):
        if isinstance(value, dict) and "$ref" in value:
            return reference(value["$ref"])
        return _literal(value)

    shapes = {"Rectangle", "Circle", "Ellipse"}
    used_shapes = set()
    lines = []
    for index, operation in enumerate(normalized["operations"]):
        entry = dict(operation)
        verb = entry.pop("op")
        parts = []
        for key, value in entry.items():
            rendered = argument(value)
            for shape in shapes:
                if rendered.startswith(shape + "("):
                    used_shapes.add(shape)
            parts.append(f"{key}={rendered}")
        call = f"{variable}.{verb}({', '.join(parts)})"
        lines.append((f"op{index} = " if index in referenced else "") + call)

    wafer_arguments = ", ".join(
        f"{key}={argument(value)}"
        for key, value in normalized["wafer"].items())
    for shape in shapes:
        if f"{shape}(" in wafer_arguments:
            used_shapes.add(shape)

    imports = ["Wafer"] + sorted(used_shapes)
    source = [
        '"""Generated by semi-structures from a process document.',
        "",
        "Edit freely: this is ordinary package code, and re-running it",
        "reproduces the same model.",
        '"""',
        f"from semi_structures import {', '.join(imports)}",
        "",
        "",
        f"{variable} = Wafer({wafer_arguments})",
        *lines,
        "",
        f'{variable}.render(path="structure.png", labels="all",',
        "         print_width_in=6.3)",
        "",
    ]
    return {"source": "\n".join(source), "operations": len(lines),
            "backend": wafer.select_backend("auto")}


TOOLS = (list_materials, get_material, list_examples, get_example,
         validate_process, inspect_structure, render_structure, export_python)
