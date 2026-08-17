"""API checks for the optional true-solid backend."""

import importlib.util
import unittest


SOLID_AVAILABLE = all(
    importlib.util.find_spec(name) is not None for name in ("pyvista", "trimesh")
)


@unittest.skipUnless(SOLID_AVAILABLE, "solid dependencies are not installed")
class SolidApiTests(unittest.TestCase):
    def test_solid_scene_accepts_geometry_and_labels(self):
        from semi_structures.solid import Scene

        scene = Scene()
        handle = scene.box((0, 0, 0), (100, 80, 20), "Si")
        scene.label("substrate", anchor=(50, 40, 20), position=(0.8, 0.4))

        self.assertIsNotNone(handle)
        self.assertEqual(len(scene.parts), 1)
        self.assertEqual(len(scene.labels), 1)

    def test_booleans_tolerate_parts_that_are_cut_away(self):
        import trimesh
        from semi_structures.solid import Scene

        scene = Scene()
        gone = scene.box((0, 0, 0), (2, 2, 1), "Si")
        keep = scene.box((5, 5, 0), (2, 2, 1), "W")
        scene.cut(gone, trimesh.creation.box(extents=(4, 4, 4)))
        self.assertIsNone(scene.parts[gone][0])
        scene.drill_hole(1, 1, 0.3)             # must not raise on the void
        scene.drill_rect(5.5, 5.5, 0.4, 0.4)    # cuts the survivor
        scene.cutaway(x=5.2)                    # removes the half-space x > 5.2
        self.assertTrue(scene.parts[keep][0].is_watertight)
        lo, hi = scene.bounds()
        self.assertLessEqual(hi[0], 5.2 + 1e-9)
        self.assertAlmostEqual(lo[0], 5.0)

    def test_text_sizes_are_points_at_print_width(self):
        from semi_structures.solid import Scene
        from semi_structures.style import MIN_PRINT_PT

        scene = Scene()
        scene.box((0, 0, 0), (10, 8, 2), "Si")
        with self.assertRaises(ValueError):
            scene.label("too small", anchor=(5, 4, 2), position=(0.8, 0.4),
                        size=MIN_PRINT_PT - 0.5)
        with self.assertRaises(ValueError):
            scene.text2d("too small", size=MIN_PRINT_PT - 0.5)
        with self.assertWarns(DeprecationWarning):
            scene.label("legacy", anchor=(5, 4, 2), position=(0.8, 0.4),
                        font_size=8)
        # window derives from print width x dpi; px per point follows.
        window, px_per_pt = Scene._window(None, 6.3, 300, 0.75)
        self.assertEqual(window, (1890, 1418))
        self.assertAlmostEqual(px_per_pt, 1890 / (6.3 * 72))
        window, px_per_pt = Scene._window((900, 720), 3.0, 300, 0.75)
        self.assertEqual(window, (900, 720))
        self.assertAlmostEqual(px_per_pt, 900 / (3.0 * 72))

    def test_process_auto_selects_boolean_solids_for_shaped_etch_and_fill(self):
        from math import pi

        from semi_structures.process import Circle, Ellipse, Rectangle, Wafer

        wafer = Wafer(size=(100, 80), substrate="Si", thickness=20)
        wafer.add_layer("SiO2", 10)
        wafer.add_layer("Si3N4", 10)
        rectangle = wafer.etch(Rectangle((20, 20), (12, 8)), depth=15)
        circle = wafer.etch(Circle((50, 45), 5))
        ellipse = wafer.etch(Ellipse((78, 22), (6, 3), rotation=30), depth=20)
        wafer.fill(rectangle, "Cu")
        wafer.fill(circle, "W", overfill=2)
        wafer.fill(ellipse, "SiP")

        self.assertEqual(wafer.select_backend(), "solid")
        self.assertEqual(circle.z0, wafer.substrate_top)
        with self.assertRaises(ValueError):
            wafer.select_backend("vector")

        scene = wafer.model()
        self.assertEqual(len(scene.parts), 6)
        self.assertTrue(all(part[0].is_watertight for part in scene.parts))

        original_volume = 100 * 80 * 40
        expected_overfill = pi * 5**2 * 2
        modeled_volume = sum(part[0].volume for part in scene.parts)
        self.assertAlmostEqual(modeled_volume,
                               original_volume + expected_overfill,
                               delta=4.0)

    def test_render_dispatches_solid_flows_with_callouts(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from semi_structures import Circle, Wafer, nm, um

        wafer = Wafer(size=(2 * um, 1.5 * um), substrate="Si",
                      thickness=400 * nm, name="Si")
        wafer.add_layer("SiO2", 120 * nm, name="oxide")
        via = wafer.etch(Circle((1 * um, 0.75 * um), diameter=300 * nm),
                         stop_on="Si", name="via")
        wafer.fill(via, "Cu", overfill=40 * nm, name="Cu plug")

        fig, ax = plt.subplots()
        scene = wafer.render(ax=ax, labels=["oxide", "Cu plug"],
                             print_width_in=3.0, window=(300, 240))
        self.assertEqual(len(scene.labels), 2)
        self.assertEqual(len(ax.images), 1)
        plt.close(fig)

    def test_stack_break_cuts_solids_and_brackets_the_block(self):
        from math import pi
        from semi_structures import Circle, Wafer

        wafer = Wafer(size=(100, 80), substrate="Si", thickness=20)
        wafer.add_multilayer([("SiO2", 2.0), ("Si3N4", 3.0)], repeats=40,
                             show=(4, 2), gap=8.0, name="ON")
        hole = wafer.etch(Circle((50, 40), 5), depth=wafer.top - 20)
        wafer.fill(hole, "Si")
        scene = wafer.model()                    # circle -> solid
        volume = sum(p[0].volume for p in scene.parts if p[0] is not None)
        drawn = 100 * 80 * (20 + 6 * 5.0)      # break interval removed
        self.assertAlmostEqual(volume, drawn, delta=2.0)
        # every live part stays outside the break interval
        brk = wafer.breaks[0]
        for mesh, _, _ in scene.parts:
            if mesh is None:
                continue
            zc = 0.5 * (mesh.bounds[0][2] + mesh.bounds[1][2])
            self.assertFalse(brk.z0 + 1e-6 < zc < brk.z1 - 1e-6)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        scene = wafer.render(ax=ax, print_width_in=3.0, window=(300, 240))
        self.assertEqual(len(scene.brackets), 1)
        self.assertIn("34 not drawn", scene.brackets[0]["text"])
        plt.close(fig)

    def test_wafer_notch_and_flat_cut_inheriting_films_only(self):
        from math import pi, sin, sqrt
        from semi_structures import Circle, Wafer

        def volume(scene):
            return sum(p[0].volume for p in scene.parts if p[0] is not None)

        polygon_area = lambda r: 0.5 * 96 * r ** 2 * sin(2 * pi / 96)
        # V-notch: substrate + one blanket film lose the notch prism, the
        # local pad keeps its full volume
        w = Wafer(size=300, shape="circle", substrate="Si", thickness=20,
                  notch="V", notch_depth=12)
        w.add_layer("SiO2", 5)
        w.add_layer("Al", 2, shape=Circle((150, 150), 40))
        v = volume(w.model())
        full = polygon_area(150) * 25 + polygon_area(40) * 2
        notch = 12 * 12 * 25                  # 90-degree V: base 2d, depth d
        self.assertLess(v, full)
        self.assertGreater(v, full - 1.6 * notch)   # rim curvature adds a bit
        with self.assertRaises(ValueError):
            Wafer(size=(10, 8), notch="V")
        with self.assertRaises(ValueError):
            Wafer(size=100, shape="circle", notch="round")

        # flat: the removed segment area x height, at the requested angle
        L = 97.5                                # 32.5 % of 300
        w = Wafer(size=300, shape="circle", substrate="Si", thickness=10,
                  notch="flat", flat_length=L, notch_angle=0.0)
        v = volume(w.model())
        r, half = 150.0, L / 2
        d = r - sqrt(r * r - half * half)
        theta = 2 * __import__("math").asin(half / r)
        segment = 0.5 * r * r * (theta - sin(theta))
        self.assertAlmostEqual(v, (polygon_area(r) - segment) * 10,
                               delta=0.02 * polygon_area(r) * 10)
        lo, hi = w.model().bounds()
        self.assertAlmostEqual(hi[0], 150 + r - d, delta=0.5)   # flat at +x

    def test_cone_frustum_geometry(self):
        """cone() builds a closed frustum whose volume matches the analytic
        value, accepts radii or diameters, and refuses degenerate input."""
        import math

        from semi_structures.solid import Scene

        s = Scene()
        frustum = s.parts[s.cone((0, 0), 0.0, 2.0, "W",
                                 r_bottom=0.8, r_top=0.4)][0]
        cone = s.parts[s.cone((3, 0), 0.0, 2.0, "Cu",
                              r_bottom=0.8, r_top=0.0)][0]
        inverted = s.parts[s.cone((6, 0), 0.0, 2.0, "Al",
                                  r_bottom=0.0, r_top=0.8)][0]
        by_diameter = s.parts[s.cone((9, 0), 0.0, 2.0, "Si",
                                     d_bottom=1.6, d_top=0.8)][0]

        for mesh in (frustum, cone, inverted, by_diameter):
            self.assertTrue(mesh.is_watertight)
            self.assertAlmostEqual(mesh.bounds[0][2], 0.0, places=6)
            self.assertAlmostEqual(mesh.bounds[1][2], 2.0, places=6)

        # V = pi h (R^2 + R r + r^2) / 3, within the polygonal approximation
        expected = math.pi * 2.0 / 3 * (0.8 ** 2 + 0.8 * 0.4 + 0.4 ** 2)
        self.assertAlmostEqual(frustum.volume, expected, delta=0.01 * expected)
        expected_cone = math.pi * 0.8 ** 2 * 2.0 / 3
        self.assertAlmostEqual(cone.volume, expected_cone,
                               delta=0.01 * expected_cone)
        # a diameter is just another way of saying the same radius
        self.assertAlmostEqual(by_diameter.volume, frustum.volume, places=6)
        # point-down is the same solid, flipped
        self.assertAlmostEqual(inverted.volume, cone.volume, places=6)

        with self.assertRaises(ValueError):          # both forms at once
            s.cone((0, 0), 0.0, 1.0, "W", r_top=0.5, d_top=1.0, r_bottom=0.5)
        with self.assertRaises(ValueError):          # neither form
            s.cone((0, 0), 0.0, 1.0, "W", r_bottom=0.5)
        with self.assertRaises(ValueError):          # no solid at all
            s.cone((0, 0), 0.0, 1.0, "W", r_bottom=0.0, r_top=0.0)
        with self.assertRaises(ValueError):          # negative radius
            s.cone((0, 0), 0.0, 1.0, "W", r_bottom=-1.0, r_top=0.2)
        with self.assertRaises(ValueError):          # zero height
            s.cone((0, 0), 0.0, 0.0, "W", r_bottom=1.0, r_top=0.2)

        # the cylinder gained the same diameter spelling
        wide = s.parts[s.cylinder((0, 9), 0.0, h=1.0, material="W",
                                  diameter=2.0)][0]
        self.assertAlmostEqual(wide.bounds[1][0] - wide.bounds[0][0], 2.0,
                               places=2)

    def test_labelled_coordinate_axes(self):
        """Scene.axes() sizes itself from the model, accepts an explicit
        placement, and refuses a scene it cannot measure."""
        from semi_structures.solid import Scene
        from semi_structures.style import MIN_PRINT_PT

        s = Scene()
        s.box((0, 0, 0), (10, 6, 2), "Si")
        s.axes()
        triad = s.triads[0]
        # placed outside the minimum corner, so it sits beside the structure
        self.assertLess(triad["origin"][0], 0.0)
        self.assertLess(triad["origin"][1], 0.0)
        self.assertEqual(triad["origin"][2], 0.0)
        self.assertGreater(triad["length"], 0.0)
        self.assertEqual(triad["labels"], ["x", "y", "z"])

        s.axes(origin=(1, 2, 3), length=4.0, labels=("a", "b", "c"))
        self.assertEqual(list(s.triads[1]["origin"]), [1.0, 2.0, 3.0])
        self.assertEqual(s.triads[1]["labels"], ["a", "b", "c"])

        s.axes(origin=(0, 0, 0), length=1.0, labels=None)
        self.assertIsNone(s.triads[2]["labels"])

        with self.assertRaises(ValueError):          # nothing to measure
            Scene().axes()
        with self.assertRaises(ValueError):          # below the print floor
            s.axes(size=MIN_PRINT_PT - 1)
        with self.assertRaises(ValueError):
            s.axes(origin=(0, 0, 0), length=0)
        with self.assertRaises(ValueError):
            s.axes(origin=(0, 0, 0), length=1.0, labels=("x", "y"))

        img = s.render_array(print_width_in=2.0, window=(220, 170))
        self.assertEqual(img.shape[:2], (170, 220))

    def test_transparent_crystals_default_to_their_alpha(self):
        """``Scene.add``/``box`` take ``style.alpha_for`` when ``opacity`` is
        None; an explicit opacity still wins; the DSL scene inherits it."""
        from semi_structures import Wafer
        from semi_structures.solid import Scene
        from semi_structures.style import alpha_for

        s = Scene()
        h_sap = s.box((0, 0, 0), (4, 4, 1), "sapphire")
        h_gan = s.box((0, 0, 1), (4, 4, 1), "GaN")
        h_hex = s.box((0, 0, 2), (4, 4, 1), "#123456")
        h_over = s.box((0, 0, 3), (4, 4, 1), "sapphire", opacity=1.0)
        self.assertEqual(s.parts[h_sap][2], alpha_for("sapphire"))
        self.assertEqual(s.parts[h_gan][2], 1.0)
        self.assertEqual(s.parts[h_hex][2], 1.0)
        self.assertEqual(s.parts[h_over][2], 1.0)
        w = Wafer(size=10.0, substrate="SiC-wafer", thickness=1.0,
                  shape="circle")                     # circular -> solid
        w.add_layer("GaN", 0.5)
        ops = [p[2] for p in w.scene().parts]
        self.assertIn(alpha_for("SiC-wafer"), ops)
        img = s.render_array(print_width_in=2.0, window=(160, 120))
        self.assertEqual(img.shape[:2], (120, 160))

    def test_exploded_view_guide_lines_are_empty_world_labels(self):
        """An empty-text world-mode label draws only its 3D leader -- the
        idiom fig_gpu_cowos_exploded.py uses for exploded-view guide lines
        -- and the exploded build separates every level."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
        import fig_gpu_cowos_exploded as fx

        s = fx.build(explode=16.0, labels=False)
        guides = [l for l in s.labels if l["text"] == ""]
        self.assertEqual(len(guides), 8)                     # 4 + 4 corners
        self.assertTrue(all(g["mode"] == "world" for g in guides))
        # a guide spans the gap it annotates
        g = guides[0]
        self.assertGreater(abs(g["anchor"][2] - g["position"][2]), 15.0)
        # exploded: interposer bottom sits above the C4 bump tops, dies
        # above the microbump tops; assembled: no gap
        lo, hi = s.bounds()
        self.assertGreater(hi[2], fx.SUB[2] + 2 * 16.0)
        a = fx.build(explode=0.0, labels=False)
        _, hi_a = a.bounds()
        self.assertLess(hi_a[2], fx.SUB[2] + fx.INT[2] + fx.HBM_H + 3.0)
        # renders (with 8.2 pt callouts) at a small window without error
        img = fx.build(explode=16.0).render_array(print_width_in=2.0,
                                                  window=(240, 170))
        self.assertEqual(img.shape[:2], (170, 240))

    def test_bowed_slabs_and_stick_and_ball_labels(self):
        from semi_structures.solid import Scene

        s = Scene()
        flat = s.box((0, 0, 0), (10, 7, 1), "Si")
        dome = s.box((0, 0, 0), (10, 7, 1), "Si", bow=(0.8, 0.5))
        bowl = s.box((0, 0, 0), (10, 7, 1), "Si", bow=-0.6)
        vf, vd, vb = (s.parts[h][0] for h in (flat, dome, bowl))
        # a pure vertical displacement field keeps the volume and watertightness
        self.assertTrue(vd.is_watertight and vb.is_watertight)
        self.assertAlmostEqual(vd.volume, vf.volume, delta=0.02 * vf.volume)
        # dome: centre high, corners low; bowl: the reverse
        zc = vd.vertices[:, 2]
        centre = vd.vertices[(abs(vd.vertices[:, 0] - 5) < 0.3)
                             & (abs(vd.vertices[:, 1] - 3.5) < 0.3)]
        corner = vd.vertices[(vd.vertices[:, 0] < 0.3) & (vd.vertices[:, 1] < 0.3)]
        self.assertGreater(centre[:, 2].max(), corner[:, 2].max() + 1.0)
        centre_b = vb.vertices[(abs(vb.vertices[:, 0] - 5) < 0.3)
                               & (abs(vb.vertices[:, 1] - 3.5) < 0.3)]
        corner_b = vb.vertices[(vb.vertices[:, 0] < 0.3) & (vb.vertices[:, 1] < 0.3)]
        self.assertLess(centre_b[:, 2].max(), corner_b[:, 2].max() - 0.4)
        # stick-and-ball marker is recorded and rendered without error
        s.label("film", anchor=(5, 3.5, 1), position=(0.9, 0.2), marker="dot",
                marker_size=3.0)
        self.assertEqual(s.labels[-1]["marker"], "dot")
        img = s.render_array(print_width_in=2.0, window=(200, 160))
        self.assertEqual(img.shape[:2], (160, 200))

    def test_circular_wafer_and_blanket_films_are_true_cylinders(self):
        from math import pi, sin

        from semi_structures.process import Circle, Wafer

        wafer = Wafer(size=300, shape="circle", substrate="Si", thickness=20)
        wafer.add_layer("SiO2", 5)
        wafer.add_layer("Al", 2, shape=Circle((150, 150), 100))

        self.assertEqual(wafer.select_backend(), "solid")
        scene = wafer.model()
        polygon_area = lambda radius: 0.5 * 96 * radius**2 * sin(2 * pi / 96)
        expected = polygon_area(150) * 25 + polygon_area(100) * 2
        self.assertAlmostEqual(sum(part[0].volume for part in scene.parts),
                               expected, delta=0.1)

    def test_implant_replaces_material_without_adding_volume(self):
        from semi_structures.process import Rectangle, Wafer

        wafer = Wafer(size=(100, 80), substrate="Si", thickness=20)
        wafer.implant(Rectangle((30, 40), (20, 30)), "SiP", depth=6)

        self.assertEqual(wafer.select_backend(), "solid")
        scene = wafer.model()
        self.assertAlmostEqual(sum(part[0].volume for part in scene.parts),
                               100 * 80 * 20, delta=0.1)
        self.assertEqual(len(scene.parts), 2)
        with self.assertRaises(ValueError):
            wafer.boxes()

    def test_mesa_and_backside_layer_use_boolean_geometry(self):
        from semi_structures.process import Rectangle, Wafer

        wafer = Wafer(size=(100, 80), substrate="SiC", thickness=20)
        wafer.add_layer("GaN", 8)
        wafer.add_backside_layer("Ni", 2)
        fields = wafer.mesa(Rectangle((50, 40), (40, 30)), depth=8,
                            name="active mesa")

        self.assertEqual(len(fields), 4)
        self.assertEqual(wafer.top, 28)
        self.assertEqual(wafer.bottom, -2)
        # A rectangular mesa is exact in vector; the solid model is opt-in.
        self.assertEqual(wafer.select_backend(), "vector")
        scene = wafer.model(backend="solid")
        expected_volume = 100 * 80 * 22 + 40 * 30 * 8
        self.assertAlmostEqual(sum(part[0].volume for part in scene.parts),
                               expected_volume, delta=0.1)

    def test_local_feature_can_be_placed_at_an_explicit_height(self):
        from semi_structures.process import Circle, Wafer

        wafer = Wafer(size=(100, 80), substrate="Si", thickness=20)
        feature = wafer.add_feature("W", Circle((50, 40), 8), 4, z0=6)

        self.assertEqual(feature.z0, 6)
        self.assertEqual(wafer.top, 20)
        self.assertEqual(wafer.select_backend(), "solid")

    def test_local_feature_can_be_etched_from_its_own_surface(self):
        from semi_structures.process import Rectangle, Wafer

        wafer = Wafer(size=(100, 80), substrate="Si", thickness=20)
        wafer.add_feature("TiN", Rectangle((50, 40), (30, 20)), 8)
        opening = wafer.etch(Rectangle((50, 40), (20, 10)), depth=8,
                              surface_z=28)
        wafer.fill(opening, "SiO2")

        scene = wafer.model(backend="solid")
        expected = 100 * 80 * 20 + 30 * 20 * 8
        self.assertAlmostEqual(sum(part[0].volume for part in scene.parts),
                               expected, delta=0.1)


if __name__ == "__main__":
    unittest.main()
