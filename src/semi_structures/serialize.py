"""JSON serialization for the process model.

What is stored is the *recipe*, not the baked geometry: the ordered list of
DSL verb calls with their arguments, exactly as the author wrote them. Replaying
that list reconstructs every layer, hole, fill and break, so the document stays
valid even if the internal geometry representation changes, and it can be read
and edited by hand.

    from semi_structures import Wafer

    w = Wafer(size=(4.0, 2.5), substrate="Si", thickness=0.8)
    w.add_layer("SiO2", 0.2, name="oxide")
    w.etch(Rectangle((2.0, 1.25), (0.9, 2.5)), depth=0.2, name="window")

    w.to_json("cell.json")                  # write
    same = Wafer.from_json("cell.json")      # read back, identical model

A document looks like this::

    {
      "format": "semi-structures/wafer",
      "version": 1,
      "wafer": {"size": [4.0, 2.5], "substrate": "Si", "thickness": 0.8},
      "operations": [
        {"op": "add_layer", "material": "SiO2", "thickness": 0.2,
         "name": "oxide"},
        {"op": "etch", "shape": {"shape": "rectangle", "center": [2.0, 1.25],
         "size": [0.9, 2.5], "rotation": 0.0}, "depth": 0.2, "name": "window"}
      ]
    }

Feature references (``etch(stop_on=...)``, ``fill(hole)``, ``strip(layer)``)
are stored as ``{"$ref": {"op": i}}``, pointing at the operation that created
the feature -- ``{"op": -1}`` is the substrate from the constructor. A
list-producing operation such as ``add_multilayer`` is addressed with an extra
``"item"`` index. References are therefore independent of naming, and a model
whose features are unnamed round-trips just as exactly as one whose features
are all named.
"""
from __future__ import annotations

import json

FORMAT = "semi-structures/wafer"
VERSION = 1


# -- value encoding -----------------------------------------------------------

def _encode_shape(shape):
    from .process import Circle, Ellipse, Rectangle

    if isinstance(shape, Rectangle):
        return {"shape": "rectangle", "center": list(shape.center),
                "size": list(shape.size), "rotation": shape.rotation}
    if isinstance(shape, Circle):
        return {"shape": "circle", "center": list(shape.center),
                "radius": shape.radius}
    if isinstance(shape, Ellipse):
        return {"shape": "ellipse", "center": list(shape.center),
                "radii": list(shape.radii), "rotation": shape.rotation}
    raise TypeError(f"cannot serialize shape {shape!r}")


def _decode_shape(data):
    from .process import Circle, Ellipse, Rectangle

    kind = data.get("shape")
    if kind == "rectangle":
        return Rectangle(tuple(data["center"]), tuple(data["size"]),
                         float(data.get("rotation", 0.0)))
    if kind == "circle":
        return Circle(tuple(data["center"]), radius=float(data["radius"]))
    if kind == "ellipse":
        return Ellipse(tuple(data["center"]), tuple(data["radii"]),
                       float(data.get("rotation", 0.0)))
    raise ValueError(f"unknown shape kind {kind!r}")


def encode_value(value, produced):
    """Encode one argument. ``produced`` maps ``id(feature)`` to its
    ``{"op": i, "item": j}`` address."""
    from .process import (
        Circle, Ellipse, EtchFeature, FillFeature, Layer, Rectangle,
        RegionFeature, StackBreak,
    )

    if isinstance(value, (Rectangle, Circle, Ellipse)):
        return _encode_shape(value)
    if isinstance(value, (Layer, EtchFeature, FillFeature, RegionFeature,
                          StackBreak)):
        address = produced.get(id(value))
        if address is None:
            raise ValueError(
                "cannot serialize a reference to a feature this wafer did "
                "not create")
        return {"$ref": address}
    if isinstance(value, (list, tuple)):
        return [encode_value(v, produced) for v in value]
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    raise TypeError(f"cannot serialize argument of type {type(value).__name__}")


def decode_value(value, results, substrate):
    """Inverse of :func:`encode_value`; ``results[i]` is what operation ``i``
    returned during replay."""
    if isinstance(value, dict):
        if "$ref" in value:
            address = value["$ref"]
            index = address["op"]
            target = substrate if index < 0 else results[index]
            item = address.get("item")
            return target if item is None else target[item]
        if "shape" in value:
            return _decode_shape(value)
        raise ValueError(f"unrecognized object in document: {value!r}")
    if isinstance(value, list):
        return [decode_value(v, results, substrate) for v in value]
    return value


# -- documents ----------------------------------------------------------------

def wafer_to_dict(wafer):
    """The recipe of ``wafer`` as a plain JSON-ready dictionary."""
    operations = []
    for index, (verb, arguments) in enumerate(wafer._script):
        entry = {"op": verb}
        for key, value in arguments.items():
            entry[key] = encode_value(value, wafer._produced)
        operations.append(entry)
    return {"format": FORMAT, "version": VERSION,
            "wafer": {key: encode_value(value, wafer._produced)
                      for key, value in wafer._wafer_arguments.items()},
            "operations": operations}


def wafer_from_dict(data, wafer_class=None):
    """Rebuild a :class:`~semi_structures.process.Wafer` from a document."""
    if wafer_class is None:
        from .process import Wafer as wafer_class

    if not isinstance(data, dict):
        raise TypeError("a wafer document must be a JSON object")
    fmt = data.get("format")
    if fmt != FORMAT:
        raise ValueError(f"not a {FORMAT} document (format={fmt!r})")
    version = data.get("version")
    if version != VERSION:
        raise ValueError(
            f"unsupported document version {version!r}; this build reads "
            f"version {VERSION}")

    arguments = {key: decode_value(value, [], None)
                 for key, value in data.get("wafer", {}).items()}
    wafer = wafer_class(**arguments)

    results = []
    for position, entry in enumerate(data.get("operations", [])):
        entry = dict(entry)
        verb = entry.pop("op", None)
        if verb is None:
            raise ValueError(f"operation {position} has no 'op' name")
        method = getattr(wafer, verb, None)
        # Allowlist, not denylist: only methods marked as DSL verbs may be
        # replayed, so a document cannot reach any other public method.
        if not getattr(method, "_dsl_verb", False):
            raise ValueError(f"operation {position}: unknown verb {verb!r}")
        kwargs = {key: decode_value(value, results, wafer.substrate)
                  for key, value in entry.items()}
        results.append(method(**kwargs))
    return wafer


def wafer_to_json(wafer, path=None, *, indent=2):
    """Serialize to a JSON string, or write it to ``path`` and return it."""
    text = json.dumps(wafer_to_dict(wafer), indent=indent)
    if path is not None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    return text


def wafer_from_json(source, wafer_class=None):
    """Read a document from a JSON string, a path, or an open file."""
    if hasattr(source, "read"):
        data = json.load(source)
    else:
        text = str(source)
        looks_like_json = text.lstrip()[:1] == "{"
        if looks_like_json:
            data = json.loads(text)
        else:
            with open(source, encoding="utf-8") as handle:
                data = json.load(handle)
    return wafer_from_dict(data, wafer_class)
