"""Small dependency-light checks for the public package API."""

import unittest

from semi_structures import MATERIAL, Box, Wafer, alloy_color, iso
from semi_structures.style import luminance


class PublicApiTests(unittest.TestCase):
    def test_public_api_and_material_palette(self):
        self.assertTrue(MATERIAL["Si"][0].startswith("#"))
        self.assertTrue(MATERIAL["InGaN"][0].startswith("#"))
        self.assertTrue(MATERIAL["InGaAsP"][0].startswith("#"))
        self.assertEqual(MATERIAL["package"][0], "#50565D")
        self.assertEqual(MATERIAL["PCB"][0], "#2F7D4F")
        self.assertEqual(MATERIAL["Sn"], ("#B7BBC0", 1.85))
        # package is a dark grey: darker than W, but never near-black
        package_lum = luminance(MATERIAL["package"][0])
        self.assertGreater(package_lum, 0.05)
        self.assertLess(package_lum, luminance(MATERIAL["W"][0]))
        # PCB is a fill that still takes the light label (luminance <= 0.30)
        self.assertLess(luminance(MATERIAL["PCB"][0]), 0.30)
        self.assertGreater(luminance(MATERIAL["Al"][0]),
                           luminance(MATERIAL["Sn"][0]))
        self.assertGreater(luminance(MATERIAL["Sn"][0]),
                           luminance(MATERIAL["W"][0]))
        self.assertEqual(len(iso(1, 2, 3)), 2)
        box = Box((0, 0, 0), (1, 1, 1), MATERIAL["Si"][0])
        self.assertEqual(box.size, (1, 1, 1))

    def test_iso_face_labels_respect_the_print_floor(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from semi_structures.iso import LABEL_PT, draw_scene
        from semi_structures.style import MIN_PRINT_PT

        self.assertGreaterEqual(LABEL_PT, MIN_PRINT_PT)
        fig, ax = plt.subplots()
        ok = Box((0, 0, 0), (4, 3, 1), MATERIAL["Si"][0], label=("top_x", "Si"))
        self.assertEqual(ok.label_size, LABEL_PT)
        draw_scene(ax, [ok])
        bad = Box((0, 0, 0), (4, 3, 1), MATERIAL["Si"][0], label=("top_x", "Si"),
                  label_size=MIN_PRINT_PT - 1)
        with self.assertRaises(ValueError):
            draw_scene(ax, [bad])
        plt.close(fig)

    def test_sige_common_composition_uses_dark_ge_endpoint(self):
        self.assertEqual(MATERIAL["Ge"][0], "#4F7FA5")
        self.assertEqual(alloy_color("Si", "Ge", 0.30), "#91bdd2")
        self.assertGreater(luminance(MATERIAL["Si"][0]),
                           luminance(alloy_color("Si", "Ge", 0.30)))
        self.assertGreater(luminance(alloy_color("Si", "Ge", 0.30)),
                           luminance(MATERIAL["Ge"][0]))

    def test_process_deposit_etch_and_fill(self):
        wafer = Wafer(size=(1000, 800), substrate="Si", thickness=200)
        wafer.add_layer("SiO2", 50)
        opening = wafer.drill(400, 300, 100, 100, depth=50)
        wafer.fill(opening, "Cu")

        self.assertEqual(wafer.top, 250)
        self.assertEqual(opening.z0, 200)
        with self.assertWarns(DeprecationWarning):
            self.assertEqual(opening["z0"], 200)     # 0.1 dict access
        self.assertGreater(len(wafer.boxes()), 1)

    def test_tapered_etch_and_fill(self):
        """A taper cuts a frustum of the right volume, forces the solid
        backend, is inherited by the fill, and is refused when it would close
        the feature."""
        import math

        from semi_structures import Circle, Rectangle
        from semi_structures.process import _shape_prism

        # circle -> truncated cone, against the analytic volume
        depth, radius, angle = 2.0, 1.0, 8.0
        cone = _shape_prism(Circle((0, 0), radius=radius), 0.0, depth, angle)
        r_floor = radius - depth * math.tan(math.radians(angle))
        expected = (math.pi * depth / 3.0
                    * (radius ** 2 + radius * r_floor + r_floor ** 2))
        self.assertTrue(cone.is_watertight)
        self.assertAlmostEqual(cone.volume, expected, delta=0.002 * expected)
        self.assertAlmostEqual(cone.bounds[1][0] - cone.bounds[0][0],
                               2 * radius, places=3)

        # rectangle -> truncated pyramid. A constant inset leaves the two
        # rectangles dissimilar, so this is a general prismatoid:
        # V = h/6 (A_bottom + 4 A_middle + A_top).
        inset = math.tan(math.radians(15.0))
        pyramid = _shape_prism(Rectangle((0, 0), (2.0, 3.0)), 0.0, 1.0, 15.0)
        a0, b0 = 2.0 - 2 * inset, 3.0 - 2 * inset
        expected = (a0 * b0 + 4 * (0.5 * (a0 + 2.0)) * (0.5 * (b0 + 3.0))
                    + 2.0 * 3.0) / 6.0
        self.assertTrue(pyramid.is_watertight)
        self.assertAlmostEqual(pyramid.volume, expected, places=6)

        # a negative taper is re-entrant: the floor is the wider end
        flared = _shape_prism(Circle((0, 0), radius=1.0), 0.0, 1.0, -10.0)
        self.assertGreater(flared.volume, math.pi * 1.0)

        # in a flow: dispatch, inheritance and an exact vector refusal
        wafer = Wafer(size=(10, 10), substrate="Si", thickness=2.0)
        wafer.add_layer("SiO2", 1.0, name="ox")
        self.assertFalse(wafer.requires_solid)
        via = wafer.etch(Circle((5, 5), radius=0.8), depth=1.0, taper=10.0,
                         name="via")
        plug = wafer.fill(via, "W", overfill=0.2, name="plug")
        self.assertEqual(via.taper, 10.0)
        self.assertEqual(plug.taper, 10.0)          # inherited from the void
        self.assertTrue(wafer.requires_solid)
        self.assertEqual(wafer.select_backend(), "solid")
        with self.assertRaises(ValueError):
            wafer.select_backend("vector")
        self.assertGreaterEqual(len(wafer.scene().parts), 3)

        # a straight etch is unaffected
        straight = Wafer(size=(10, 10), substrate="Si", thickness=2.0)
        straight.add_layer("SiO2", 1.0)
        straight.etch(Rectangle((5, 5), (2, 2)), depth=0.5)
        self.assertFalse(straight.requires_solid)

        bad = Wafer(size=(10, 10), substrate="Si", thickness=2.0)
        with self.assertRaises(ValueError):         # closes over the depth
            bad.etch(Circle((5, 5), radius=0.5), depth=1.0, taper=60.0)
        with self.assertRaises(ValueError):         # not a sidewall angle
            bad.etch(Circle((5, 5), radius=0.5), depth=1.0, taper=90.0)

    def test_feature_references_names_and_units(self):
        from semi_structures import (
            Circle, FillFeature, Layer, Rectangle, mm, nm, um)

        self.assertEqual((um, mm), (1000 * nm, 1_000_000 * nm))
        wafer = Wafer(size=(2 * um, 1.5 * um), substrate="Si",
                      thickness=500 * nm)
        oxide = wafer.add_layer("SiO2", 50 * nm, name="oxide")
        legacy = wafer.add_layer("Si3N4", 20 * nm, label="cap")   # 0.1 alias
        stack = wafer.add_multilayer([("SiO2", 5 * nm), ("W", 5 * nm)],
                                     repeats=2, name="ON")
        via = wafer.etch(Circle((1 * um, 0.75 * um), diameter=120 * nm),
                         stop_on="oxide", name="via")
        cu = wafer.fill("via", "Cu", overfill=20 * nm, name="Cu via")
        pad = wafer.add_pad("Al", 100 * nm, 100 * nm, 300 * nm, 200 * nm,
                            30 * nm, name="pad")

        self.assertIsInstance(oxide, Layer)
        self.assertEqual((oxide.kind, oxide.name, oxide.top),
                         ("layer", "oxide", 550 * nm))
        self.assertEqual(legacy.name, "cap")
        self.assertEqual([layer.name for layer in stack],
                         ["ON 1", "ON 2", "ON 3", "ON 4"])
        self.assertEqual(via.z0, oxide.top)          # stop_on by name
        self.assertIsInstance(cu, FillFeature)
        self.assertEqual(cu.top, via.z1 + 20 * nm)
        self.assertEqual(pad.kind, "feature")
        self.assertEqual(pad.footprint.corner, (100 * nm, 100 * nm))
        self.assertIs(wafer.find("Cu via"), cu)
        self.assertEqual(wafer.features[0], wafer.substrate)
        self.assertEqual(len(wafer.features), 1 + 2 + 4 + 1 + 1 + 1)
        self.assertEqual(wafer.fills, (cu,))
        with self.assertRaises(KeyError):
            wafer.find("nope")
        self.assertEqual(Rectangle.from_corner(0, 0, 4, 2).center, (2.0, 1.0))
        with self.assertRaises(ValueError):
            Circle((0, 0), radius=1, diameter=2)

    def test_vector_draw_order_is_geometric(self):
        """Buried features draw before the films that cover them."""
        from semi_structures.process import Rectangle
        from semi_structures.style import MATERIAL as M

        # A W pad buried inside the substrate, then an oxide on top: the
        # oxide (z0=2) must be painted after the pad (z0=1).
        wafer = Wafer(size=(10, 8), substrate="Si", thickness=2)
        wafer.add_feature("W", Rectangle((5, 4), (2, 2)), 0.5, z0=1.0)
        wafer.add_layer("SiO2", 1)
        order = [b.color for b in sorted(wafer.boxes(),
                                         key=lambda b: b.depth_key())]
        self.assertLess(order.index(M["W"][0]), order.index(M["SiO2"][0]))

        # A Cu via in the oxide, then Al deposited over it: the Al (z0=3)
        # must be painted after the Cu (z0=2), which sorts among the oxide
        # cells around it.
        wafer = Wafer(size=(10, 8), substrate="Si", thickness=2)
        wafer.add_layer("SiO2", 1)
        via = wafer.drill(4, 3, 2, 2, depth=1)
        wafer.fill(via, "Cu")
        wafer.add_layer("Al", 0.5)
        boxes = sorted(wafer.boxes(), key=lambda b: b.depth_key())
        colors = [b.color for b in boxes]
        self.assertEqual(colors[-1], M["Al"][0])
        self.assertTrue(all(b.k == 0 for b in boxes))

    def test_render_draws_vector_flows_with_automatic_callouts(self):
        import os
        import tempfile
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from semi_structures import Rectangle

        wafer = Wafer(size=(10, 7), substrate="Si", thickness=1.2,
                      name="Si substrate")
        wafer.add_layer("SiO2", 0.5, name="oxide")
        wafer.add_pad("W", 1, 1, 3, 2, 0.6, name="W pad")
        wafer.add_feature("Cu", Rectangle.from_corner(6, 3.5, 3, 2.5), 0.8,
                          name="Cu pad")

        fig, ax = plt.subplots()
        boxes = wafer.render(ax=ax, labels="all")
        self.assertEqual(len(boxes), 4)
        texts = sorted(t.get_text() for t in ax.texts)
        self.assertEqual(texts, ["Cu pad", "Si substrate", "W pad", "oxide"])
        plt.close(fig)

        fig, ax = plt.subplots()
        wafer.render(ax=ax, labels=["W pad"])
        self.assertEqual([t.get_text() for t in ax.texts], ["W pad"])
        plt.close(fig)

        with self.assertRaises(KeyError):
            wafer.render(ax=plt.figure().gca(), labels=["nope"])
        with self.assertRaises(ValueError):
            wafer.render()

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "flow.png")
            wafer.render(path=path, labels="all")
            self.assertGreater(os.path.getsize(path), 0)

    def test_vector_path_is_exact_for_rectilinear_etches(self):
        """boxes() splits solids at etch limits so partial-depth etches,
        etches into fills, and mesas render exactly -- and rectilinear flows
        therefore stay on the vector backend."""
        from semi_structures import Rectangle

        def volume(boxes):
            return sum(b.size[0] * b.size[1] * b.size[2] for b in boxes)

        # partial-depth pit, unfilled: the oxide loses exactly the pit volume
        wafer = Wafer(size=(10, 8), substrate="Si", thickness=2)
        wafer.add_layer("SiO2", 1.0)
        wafer.etch(Rectangle((5, 4), (2, 2)), depth=0.4)
        self.assertEqual(wafer.select_backend(), "vector")
        self.assertAlmostEqual(volume(wafer.boxes()),
                               10 * 8 * 3 - 2 * 2 * 0.4)

        # nested fills: a wide oxide-filled trench, then a narrower fill cut
        # into that oxide -- the inner fill must displace oxide, not overlap
        wafer = Wafer(size=(10, 8), substrate="Si", thickness=2)
        wafer.add_layer("Si3N4", 1.0)
        outer = wafer.etch(Rectangle((5, 4), (4, 2)), depth=1.0)
        wafer.fill(outer, "SiO2")
        inner = wafer.etch(Rectangle((5, 4), (2, 1)), depth=0.6)
        wafer.fill(inner, "W")
        boxes = wafer.boxes()
        self.assertEqual(wafer.select_backend(), "vector")
        self.assertAlmostEqual(volume(boxes), 10 * 8 * 3)   # conserved
        w_vol = sum(b.size[0] * b.size[1] * b.size[2] for b in boxes
                    if b.color == MATERIAL["W"][0])
        self.assertAlmostEqual(w_vol, 2 * 1 * 0.6)

        # mesa: four field etches leave the mesa standing, exact in vector
        wafer = Wafer(size=(10, 8), substrate="SiC", thickness=2)
        wafer.add_layer("GaN", 1.0)
        wafer.mesa(Rectangle((5, 4), (4, 3)), depth=1.0)
        self.assertEqual(wafer.select_backend(), "vector")
        self.assertAlmostEqual(volume(wafer.boxes()), 10 * 8 * 2 + 4 * 3 * 1)

    def test_lattices(self):
        import math
        from semi_structures import hex_lattice, square_lattice

        sq = square_lattice((0, 8), (0, 6), 1.0, margin=0.5)
        self.assertEqual(len(sq), 8 * 6)
        self.assertEqual(sq[0], (0.5, 0.5))
        hx = hex_lattice((0, 8), (0, 6), 1.0, margin=0.5)
        nearest = min(math.dist(a, b) for i, a in enumerate(hx)
                      for b in hx[i + 1:])
        self.assertAlmostEqual(nearest, 1.0)          # close-packed
        xs = [x for x, _ in hx]
        ys = [y for _, y in hx]
        self.assertGreaterEqual(min(xs), 0.5)
        self.assertLessEqual(max(xs), 7.5)
        self.assertGreaterEqual(min(ys), 0.5)
        self.assertLessEqual(max(ys), 5.5)
        rows = sorted(set(round(y, 6) for y in ys))
        self.assertAlmostEqual(rows[1] - rows[0], math.sqrt(3) / 2, places=5)
        hy = hex_lattice((0, 8), (0, 6), 1.0, margin=0.5, axis="y")
        self.assertEqual(len(hy), len(hex_lattice((0, 6), (0, 8), 1.0,
                                                  margin=0.5)))

    def test_stack_break_elides_repeats_in_vector_and_solid(self):
        from semi_structures import Rectangle
        from semi_structures.process import StackBreak

        pair = [("SiO2", 2.0), ("Si3N4", 3.0)]
        wafer = Wafer(size=(10, 8), substrate="Si", thickness=4)
        layers = wafer.add_multilayer(pair, repeats=100, show=(10, 5),
                                      gap=6.0, name="ON", unit="pairs")
        self.assertEqual(len(layers), 15 * 2)          # only drawn repeats
        self.assertEqual(layers[0].name, "ON 1")
        self.assertEqual(layers[-1].name, "ON 200")    # true indices kept
        brk = wafer.breaks[0]
        self.assertIsInstance(brk, StackBreak)
        self.assertEqual((brk.hidden, brk.total), (85, 100))
        self.assertEqual((brk.z0, brk.z1), (4 + 10 * 5.0, 4 + 10 * 5.0 + 6.0))
        self.assertEqual(brk.span, (4.0, 4 + 15 * 5.0 + 6.0))
        self.assertIn("85 not drawn", brk.caption)
        self.assertEqual(wafer.top, brk.span[1])
        # a slit through the drawn stack is cut at the break in vector ...
        slit = wafer.etch(Rectangle((5, 4), (1, 8)), depth=wafer.top - 4)
        wafer.fill(slit, "SiO2")
        boxes = wafer.boxes()
        self.assertFalse(any(brk.z0 - 1e-9 < b.origin[2] < brk.z1 - 1e-9
                             for b in boxes))            # nothing in the gap
        drawn = 10 * 8 * (4 + 15 * 5.0)                  # substrate + 15 pairs
        self.assertAlmostEqual(sum(b.size[0] * b.size[1] * b.size[2]
                                   for b in boxes), drawn)
        # ... and breaks are not auto-labelled
        self.assertNotIn(brk, wafer._label_features("all"))

    def test_section_renderer_is_exact_at_the_plane(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from semi_structures import Circle, Rectangle
        from semi_structures.section import chord, section_pieces

        # chords: rectangle, circle, rotated ellipse
        self.assertEqual(chord(Rectangle((5, 4), (2, 2)), 4.5), (4.0, 6.0))
        self.assertIsNone(chord(Rectangle((5, 4), (2, 2)), 6.0))
        x0, x1 = chord(Circle((5, 4), 1.0), 4.0)
        self.assertAlmostEqual(x1 - x0, 2.0)
        x0, x1 = chord(Circle((5, 4), 1.0), 4.6)
        self.assertAlmostEqual(x1 - x0, 2 * (1 - 0.36) ** 0.5)
        from semi_structures import Ellipse
        x0, x1 = chord(Ellipse((5, 4), (2, 1), rotation=90), 4.0)
        self.assertAlmostEqual(x1 - x0, 2.0, places=3)

        # a via through the oxide, a buried break, an implant: areas add up
        wafer = Wafer(size=(10, 8), substrate="Si", thickness=2, name="Si")
        wafer.add_multilayer([("SiO2", 0.5), ("Si3N4", 0.5)], repeats=10,
                             show=(2, 1), gap=1.0, name="ON")
        via = wafer.etch(Circle((5, 4), 1.0), depth=wafer.top - 2, name="via")
        wafer.fill(via, "W", name="plug")
        wafer.implant(Rectangle((2, 4), (2, 8)), "SiP", depth=1.0)
        pieces, breaks, (bx0, bx1, bz0, bz1) = section_pieces(wafer, y=4.0)
        area = sum((x1 - x0) * (z1 - z0) for p in pieces
                   for x0, x1, z0, z1 in p["rects"])
        drawn_h = 2 + 3 * 1.0                     # substrate + 3 drawn pairs
        self.assertAlmostEqual(area, 10 * drawn_h)          # nothing lost/dup
        self.assertEqual(len(breaks), 1)
        brk = breaks[0]
        for p in pieces:                                    # gap is empty
            for x0, x1, z0, z1 in p["rects"]:
                zm = 0.5 * (z0 + z1)
                self.assertFalse(brk.z0 < zm < brk.z1)
        w_area = sum((x1 - x0) * (z1 - z0) for p in pieces
                     if p["feature"].name == "plug"
                     for x0, x1, z0, z1 in p["rects"])
        self.assertAlmostEqual(w_area, 2.0 * (3 * 1.0 - 0.0))   # chord x height

        fig, ax = plt.subplots()
        out = wafer.render(ax=ax, view="section", labels=["Si", "plug"])
        self.assertTrue(out)
        self.assertEqual(sorted(t.get_text() for t in ax.texts
                                if "not drawn" not in t.get_text()),
                         ["Si", "plug"])
        plt.close(fig)

    def test_transparent_crystals_carry_alpha_through_every_renderer(self):
        """``sapphire`` and ``SiC-wafer`` are near-clear tints with a drawing
        alpha; ``Wafer.boxes()`` (vector), the section pieces and the
        palette all expose it, opaque materials and raw hex stay at 1.0."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from semi_structures import MATERIAL_ALPHA, alpha_for
        from semi_structures.section import draw_section, section_pieces
        from semi_structures.style import FAMILIES, validate_materials

        validate_materials()                        # new family obeys the laws
        self.assertEqual(alpha_for("sapphire"), MATERIAL_ALPHA["sapphire"])
        self.assertLess(alpha_for("sapphire"), 0.5)
        self.assertLess(alpha_for("SiC-wafer"), 0.6)
        self.assertEqual(alpha_for("SiC"), 1.0)      # opaque device color
        self.assertEqual(alpha_for("Al2O3"), 1.0)    # thin-film dielectric
        self.assertEqual(alpha_for("#ABCDEF"), 1.0)
        self.assertIn("SiC-wafer", dict(FAMILIES)[FAMILIES[-1][0]])
        w = Wafer(size=(10, 6), substrate="sapphire", thickness=2.0)
        w.add_layer("GaN", 1.0)
        alphas = {b.color: b.alpha for b in w.boxes()}
        self.assertEqual(alphas[MATERIAL["sapphire"][0]], alpha_for("sapphire"))
        self.assertEqual(alphas[MATERIAL["GaN"][0]], 1.0)
        pieces, _, _ = section_pieces(w, y=3.0)
        by_color = {p["color"]: p["alpha"] for p in pieces}
        self.assertEqual(by_color[MATERIAL["sapphire"][0]],
                         alpha_for("sapphire"))
        fig, ax = plt.subplots(figsize=(3, 2))
        w.render(ax=ax)                                    # vector, no error
        draw_section(ax, w, y=3.0)                         # section, no error
        plt.close(fig)

    def test_strip_removes_a_layer_everywhere(self):
        from semi_structures import Rectangle
        from semi_structures.section import section_pieces

        w = Wafer(size=(10, 6), substrate="Si", thickness=1.5, name="wafer")
        w.add_layer("SiO2", 0.5, name="film")
        resist = w.add_layer("resist", 1.0, name="resist")
        for x0, x1 in ((0, 2), (3.8, 6.2), (8, 10)):
            w.etch(Rectangle.from_corner(x0, 0, x1 - x0, 6), depth=1.0)
        top_before = w.top
        w.strip("resist")
        self.assertNotIn(resist, w.layers)
        self.assertNotIn(resist, w.features)
        self.assertEqual(w.top, top_before - 1.0)        # surface drops
        self.assertEqual(w._operations[-1][0], "strip")
        # nothing of the resist is drawn in vector or section
        self.assertFalse(any(b.color == MATERIAL["resist"][0]
                             for b in w.boxes()))
        pieces, _, _ = section_pieces(w, y=3.0)
        self.assertFalse(any(p["feature"] is resist for p in pieces))
        with self.assertRaises(ValueError):
            w.strip("film-that-does-not-exist") if False else \
                w.strip(Rectangle((1, 1), (1, 1)))
        with self.assertRaises(KeyError):
            w.strip("nope")

    def test_complete_wafer_dsl_sequence(self):
        wafer = Wafer(size=(1000, 800), substrate="Si", thickness=200)
        wafer.add_layer("SiO2", 20, label="liner")
        wafer.add_multilayer([("Si3N4", 10), ("SiO2", 8)], repeats=2)
        partial = wafer.drill(100, 100, 80, 80, depth=30)
        through = wafer.drill(700, 600, 80, 80)
        wafer.fill(partial, "Cu")
        wafer.fill(through, "SiP", overfill=15)
        wafer.add_pad("W", 300, 250, 250, 70, 25)

        self.assertGreater(partial.z0, 0)
        self.assertEqual(through.z0, 0)
        self.assertEqual(len(wafer.fills), 2)
        self.assertGreater(len(wafer.boxes()), len(wafer.layers))


if __name__ == "__main__":
    unittest.main()
