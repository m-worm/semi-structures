"""fig_hero_banner.py -- the banner at the top of the README.

Four structures across the package's range, all drawn by the true-solid
Boolean backend at one camera and one print width: a gate-all-around
nanosheet device, a 3D NAND block with a hexagonal memory-hole array, a
chip-on-wafer-on-substrate package, and a 300 mm wafer with an orientation
notch. Everything is built through the process DSL except the package, which
is an assembly rather than a fabrication flow.

The panels are rendered on a transparent background and composited, so the
banner has no frames, no titles inside the images, and one consistent light.

Outputs: ../docs/figures/hero_banner.png (+ .pdf)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Circle, Rectangle, Wafer, hex_lattice
from semi_structures.solid import Scene
from semi_structures.style import C_SLATE, PLOT_STYLE, doped

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

PANEL_W = 1.52          # printed width of one panel, inches
ASPECT = 0.88


def nanosheet():
    """A gate-all-around device: stacked Si channels through a ghosted gate.

    The channels run the long way and stick out either side of the gate, so
    the stack stays readable through the semi-transparent TiN.
    """
    s = Scene()
    s.box((0, 0, 0), (10, 8, 1.5), "Si")                      # substrate
    s.box((0, 0, 1.5), (10, 8, 0.6), "SiO2")                  # isolation
    for i in range(3):                                         # channels
        s.box((0.8, 2.6, 2.6 + i * 1.15), (8.4, 2.8, 0.55), "Si")
    # Short source/drain pads: full-height blocks would hide the very sheets
    # the panel is about.
    for x in (0.8, 7.4):
        s.box((x, 2.6, 2.1), (1.8, 2.8, 0.5), doped("Si", 0.22))
    s.box((3.9, 1.6, 2.1), (2.2, 4.8, 4.2), "TiN", opacity=0.38)
    return s, dict(azimuth=-120.0, elevation=18.0, zoom=1.22)


def nand_block():
    """A W/SiO2 stack with a hexagonal array of etched memory holes."""
    w = Wafer(size=(9.0, 7.0), substrate="Si", thickness=1.2)
    # W first so the stack ends on oxide: a light top face makes the holes
    # and the alternating side stripes read at banner size.
    w.add_multilayer([("W", 0.34), ("SiO2", 0.30)], repeats=5)
    for cx, cy in hex_lattice((1.5, 7.5), (1.4, 5.6), 1.62):
        w.etch(Circle((cx, cy), radius=0.48), through=True)
    return w.scene(), dict(azimuth=-34.0, elevation=22.0, zoom=1.24)


def package():
    """Chip on wafer on substrate: interposer, logic die, two memory stacks."""
    s = Scene()
    s.box((0, 0, 0), (13, 10, 0.9), "PCB")
    s.sphere_array((1.2, 11.8), (1.2, 8.8), 1.6, z=-0.42, r=0.42, material="Sn")
    s.box((1.0, 1.0, 0.9), (11.0, 8.0, 0.5), "substrate")    # Si interposer
    s.box((4.6, 2.2, 1.4), (5.2, 5.6, 0.9), doped("substrate", 0.14))
    for x0 in (1.7, 10.1):                                    # memory stacks
        z = 1.4
        for _ in range(6):
            s.box((x0, 2.4, z), (2.2, 5.2, 0.07), "Cu")
            s.box((x0 - 0.1, 2.3, z + 0.07), (2.4, 5.4, 0.22), "substrate")
            z += 0.29
    return s, dict(azimuth=-30.0, elevation=-14.0, zoom=1.18)


def notched_wafer():
    """A 300 mm wafer with a V-notch and two blanket films."""
    w = Wafer(size=300.0, substrate="Si", thickness=26.0, shape="circle",
              notch="V")
    w.add_layer("SiO2", 9.0)
    w.add_layer("Si3N4", 7.0)
    w.etch(Rectangle((150.0, 150.0), (120.0, 26.0)), depth=16.0)
    return w.scene(), dict(azimuth=-34.0, elevation=26.0, zoom=1.30)


PANELS = [
    (nanosheet, "gate-all-around nanosheets"),
    (nand_block, "3D NAND memory holes"),
    (package, "chip on wafer on substrate"),
    (notched_wafer, "300 mm wafer, patterned"),
]


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    width = len(PANELS) * PANEL_W
    height = PANEL_W * ASPECT + 0.24
    fig = plt.figure(figsize=(width, height))

    for index, (build, caption) in enumerate(PANELS):
        scene, camera = build()
        image = scene.render_array(print_width_in=PANEL_W, aspect=ASPECT,
                                   transparent=True, **camera)
        axes = fig.add_axes([index / len(PANELS), 0.24 / height,
                             1 / len(PANELS), 1 - 0.24 / height])
        axes.imshow(image)
        axes.set_axis_off()
        axes.text(0.5, -0.015, caption, transform=axes.transAxes,
                  fontsize=7.5, color=C_SLATE, ha="center", va="top")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "hero_banner"
    fig.savefig(f"{stem}.png", dpi=300)
    fig.savefig(f"{stem}.pdf")
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.png (+ .pdf)")


if __name__ == "__main__":
    main()
