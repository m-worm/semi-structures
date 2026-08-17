"""Round-trip tests for the JSON process document."""
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Circle, Ellipse, Rectangle, Wafer, hex_lattice
from semi_structures.serialize import FORMAT, VERSION


def build_reference():
    """A model that exercises every recorded verb."""
    w = Wafer(size=(4.0, 2.5), substrate="Si", thickness=0.8, name="wafer")
    oxide = w.add_layer("SiO2", 0.2, name="oxide")
    w.add_layer("Al", 0.35, name="metal")
    hole = w.etch(Rectangle.from_corner(0.5, 0.0, 0.9, 2.5), stop_on=oxide,
                  name="window")
    w.fill(hole, "Cu", overfill=0.1, name="plug")
    w.add_pad("W", 2.6, 0.6, 0.7, 1.0, 0.25, name="pad")
    w.add_feature("TiN", Rectangle((1.2, 1.9), (0.5, 0.4)), 0.12, name="tip")
    w.add_backside_layer("Cu", 0.15, name="back")
    w.implant(Rectangle((1.0, 1.25), (0.6, 0.8)), "SiP", depth=0.3, name="n+")
    w.mesa(Rectangle((2.0, 1.25), (2.4, 1.6)), depth=0.2, name="mesa")
    w.drill(0.2, 0.2, 0.25, 0.3, 0.2, name="via")
    w.strip("metal")
    return w


def render_digest(wafer, view="3d", **kwargs):
    figure, axes = plt.subplots(figsize=(4, 3))
    wafer.render(ax=axes, view=view, **kwargs)
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=80)
    plt.close(figure)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


class SerializationTests(unittest.TestCase):
    def test_document_shape_and_defaults(self):
        w = Wafer(size=(4.0, 2.5), substrate="Si", thickness=0.8)
        w.add_layer("SiO2", 0.2, name="oxide")
        document = w.to_dict()
        self.assertEqual(document["format"], FORMAT)
        self.assertEqual(document["version"], VERSION)
        # arguments left at their defaults are omitted, so a document reads
        # like the source that produced it
        self.assertNotIn("substrate", document["wafer"])   # "Si" is default
        self.assertNotIn("shape", document["wafer"])
        self.assertEqual(document["wafer"]["thickness"], 0.8)
        self.assertEqual(document["operations"], [
            {"op": "add_layer", "material": "SiO2", "thickness": 0.2,
             "name": "oxide"}])
        json.dumps(document)                                # is JSON-ready

    def test_round_trip_reproduces_the_model_and_the_picture(self):
        original = build_reference()
        restored = Wafer.from_json(original.to_json())

        self.assertEqual(original.to_dict(), restored.to_dict())
        self.assertEqual(original.top, restored.top)
        self.assertEqual(original.bottom, restored.bottom)
        self.assertEqual(len(original.features), len(restored.features))
        self.assertEqual(len(original.etches), len(restored.etches))
        self.assertEqual(len(original.regions), len(restored.regions))
        # the strongest statement: both models draw the same pixels
        self.assertEqual(render_digest(original), render_digest(restored))
        self.assertEqual(render_digest(original, "section", y=1.25),
                         render_digest(restored, "section", y=1.25))

    def test_round_trip_of_a_rectilinear_model_matches_box_for_box(self):
        w = Wafer(size=(4.0, 2.5), substrate="Si", thickness=0.8, name="wafer")
        oxide = w.add_layer("SiO2", 0.2, name="oxide")
        w.add_layer("Al", 0.35, name="metal")
        hole = w.etch(Rectangle.from_corner(0.5, 0.0, 0.9, 2.5),
                      stop_on=oxide, name="window")
        w.fill(hole, "Cu", overfill=0.1, name="plug")
        w.add_pad("W", 2.6, 0.6, 0.7, 1.0, 0.25, name="pad")
        w.add_backside_layer("Cu", 0.15, name="back")
        w.strip("metal")
        restored = Wafer.from_json(w.to_json())
        self.assertFalse(w.requires_solid)
        self.assertEqual(
            [(b.origin, b.size, b.color, b.alpha) for b in w.boxes()],
            [(b.origin, b.size, b.color, b.alpha) for b in restored.boxes()])
        self.assertEqual(render_digest(w), render_digest(restored))

    def test_references_survive_without_names(self):
        """stop_on / fill / strip are stored by construction order, so an
        unnamed model round-trips exactly like a named one."""
        w = Wafer(size=(4.0, 2.5), substrate="Si", thickness=0.8)
        oxide = w.add_layer("SiO2", 0.2)
        w.add_layer("Al", 0.35)
        hole = w.etch(Rectangle.from_corner(0.5, 0.0, 0.9, 2.5), stop_on=oxide)
        w.fill(hole, "Cu")
        document = w.to_dict()
        self.assertEqual(document["operations"][2]["stop_on"],
                         {"$ref": {"op": 0}})
        self.assertEqual(document["operations"][3]["hole"],
                         {"$ref": {"op": 2}})
        restored = Wafer.from_dict(document)
        self.assertEqual(restored.fills[0].opening, restored.etches[0])
        self.assertEqual(w.to_dict(), restored.to_dict())

    def test_reference_into_a_multilayer_and_to_the_substrate(self):
        w = Wafer(size=(4.0, 2.5), substrate="Si", thickness=0.8)
        stack = w.add_multilayer([("SiO2", 0.1), ("Si3N4", 0.12)], repeats=3)
        w.add_layer("Al", 0.2)
        w.etch(Rectangle((2.0, 1.25), (0.8, 0.8)), stop_on=stack[2],
               name="into-stack")
        w.etch(Rectangle((0.6, 0.6), (0.4, 0.4)), stop_on=w.substrate,
               name="to-substrate")
        document = w.to_dict()
        self.assertEqual(document["operations"][2]["stop_on"],
                         {"$ref": {"op": 0, "item": 2}})
        self.assertEqual(document["operations"][3]["stop_on"],
                         {"$ref": {"op": -1}})   # the constructor's substrate
        restored = Wafer.from_dict(document)
        self.assertEqual(w.to_dict(), restored.to_dict())
        self.assertEqual([(e.z0, e.z1) for e in w.etches],
                         [(e.z0, e.z1) for e in restored.etches])

    def test_convenience_verbs_record_the_call_the_author_wrote(self):
        """add_multilayer/mesa/add_pad/drill expand into other verbs; the
        document keeps the outer call, not the expansion."""
        w = Wafer(size=(4.0, 2.5), substrate="Si", thickness=0.8)
        w.add_multilayer([("SiO2", 0.05), ("Si3N4", 0.06)], repeats=20,
                         name="ON", show=(3, 2), gap=0.3, unit="pairs")
        w.mesa(Rectangle((2.0, 1.25), (2.0, 1.4)), depth=0.1)
        verbs = [entry["op"] for entry in w.to_dict()["operations"]]
        self.assertEqual(verbs, ["add_multilayer", "mesa"])
        restored = Wafer.from_dict(w.to_dict())
        self.assertEqual(len(w.layers), len(restored.layers))
        self.assertEqual(len(w.breaks), len(restored.breaks))
        self.assertEqual(w.breaks[0].caption, restored.breaks[0].caption)

    def test_curved_and_circular_models_round_trip(self):
        w = Wafer(size=6.0, substrate="sapphire", thickness=0.7,
                  shape="circle", notch="V")
        w.add_layer("GaN", 0.2, name="GaN")
        for cx, cy in hex_lattice((1.5, 4.5), (1.5, 4.5), 1.2)[:3]:
            w.etch(Circle((cx, cy), radius=0.22))
        w.etch(Ellipse((3.0, 3.0), (0.5, 0.25), rotation=30.0), depth=0.2)
        restored = Wafer.from_json(w.to_json())
        self.assertEqual(w.to_dict(), restored.to_dict())
        self.assertEqual(w.notch, restored.notch)
        self.assertTrue(w.requires_solid and restored.requires_solid)
        self.assertEqual(w.wafer_footprint, restored.wafer_footprint)

    def test_write_and_read_a_file(self):
        w = build_reference()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cell.json"
            text = w.to_json(path)
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(text), json.loads(path.read_text()))
            self.assertEqual(Wafer.from_json(path).to_dict(), w.to_dict())
            with open(path, encoding="utf-8") as handle:      # open file
                self.assertEqual(Wafer.from_json(handle).to_dict(), w.to_dict())

    def test_bad_documents_are_refused(self):
        w = Wafer(size=(2.0, 2.0), substrate="Si", thickness=0.5)
        good = w.to_dict()

        with self.assertRaises(ValueError):                   # wrong format
            Wafer.from_dict({**good, "format": "something/else"})
        with self.assertRaises(ValueError):                   # future version
            Wafer.from_dict({**good, "version": VERSION + 1})
        with self.assertRaises(TypeError):
            Wafer.from_dict([])
        with self.assertRaises(ValueError):                   # unknown verb
            Wafer.from_dict({**good,
                             "operations": [{"op": "vaporize", "x": 1}]})
        with self.assertRaises(ValueError):                   # no verb named
            Wafer.from_dict({**good, "operations": [{"material": "Si"}]})
        with self.assertRaises(ValueError):                   # private method
            Wafer.from_dict({**good, "operations": [{"op": "_record_layer"}]})

    def test_a_foreign_feature_cannot_be_referenced(self):
        a = Wafer(size=(2.0, 2.0), substrate="Si", thickness=0.5)
        other = Wafer(size=(2.0, 2.0), substrate="Si", thickness=0.5)
        foreign = other.add_layer("SiO2", 0.1, name="elsewhere")
        a.add_layer("Al", 0.2)
        a._script.append(("etch", {"shape": Rectangle((1.0, 1.0), (0.5, 0.5)),
                                   "stop_on": foreign}))
        with self.assertRaises(ValueError):
            a.to_dict()


if __name__ == "__main__":
    unittest.main()
