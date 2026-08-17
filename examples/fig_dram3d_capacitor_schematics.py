"""fig_dram3d_capacitor_schematics.py -- 3D DRAM capacitor schematics, two panels.

(a) vertical storage capacitors standing on access transistors over an
    array of bit lines; (b) horizontal storage capacitors on a staircase
    bit-line, the capacitor length setting the storage size.

Drawn in the schematic red / green / white scheme of the supplied reference
figure (bit lines red, transistors green, capacitors white with a red
contact band): color is ROLE and PRESENTATION here, not the book's material
palette. Geometry is the package's own; the reference is not redistributed
(provenance in examples/REFERENCES.md).

Outputs: ../docs/figures/dram3d_capacitor_schematics.pdf (+ .png)
"""
from __future__ import annotations

from math import pi
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import trimesh

from semi_structures.solid import Scene
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

RED = "#E11D1D"       # bit lines and capacitor contact bands
GREEN = "#7BC043"     # access transistors
WHITE = "#F2F2F2"     # storage capacitors


def _hcyl(scene, x0, y, z, length, r, color):
    """Horizontal cylinder along +x from x0."""
    mesh = trimesh.creation.cylinder(radius=r, height=length, sections=64)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(
        pi / 2, (0.0, 1.0, 0.0)))
    mesh.apply_translation((x0 + length / 2, y, z))
    return scene.add(mesh, color)


def vertical_capacitors():
    s = Scene()
    n, pitch = 5, 1.25
    for i in range(n):                                   # bit lines along y
        s.box((i * pitch, -0.3, 0.0), (0.55, n * pitch + 0.1, 0.35), RED)
        for j in range(n):                               # transistors
            x, y = i * pitch + 0.275, j * pitch + 0.35
            s.box((x - 0.36, y - 0.36, 0.35), (0.72, 0.72, 0.72), GREEN)
            s.cylinder((x, y), 1.07, 0.24, 0.35, RED)     # contact band
            s.cylinder((x, y), 1.42, 0.2, 5.6, WHITE)     # capacitor
    kw = dict(size=8.2)
    s.label("storage capacitors", anchor=(0.275, 0.35, 5.5),
            via=(0.16, 0.12), position=(0.03, 0.12), **kw)
    s.label("access transistors", anchor=(0.275, 0.35, 1.0),
            via=(0.16, 0.84), position=(0.03, 0.84), **kw)
    s.label("bit lines", anchor=(2.8, -0.2, 0.2),
            via=(0.55, 0.92), position=(0.55, 0.96), justify="center", **kw)
    return s


def staircase_capacitors():
    s = Scene()
    levels, dz, rows, pitch = 10, 0.62, 5, 1.05
    wall_x = 6.4
    for k in range(levels):
        z = k * dz
        length = 6.2 - 0.5 * k                            # staircase steps
        s.box((wall_x - length, -0.3, z), (length, rows * pitch + 0.1, 0.34),
              RED)
    s.box((wall_x, -0.3, 0.0), (0.6, rows * pitch + 0.1, levels * dz),
          GREEN)                                          # transistor wall
    for k in range(levels):
        zc = k * dz + 0.17 + 0.16
        for j in range(rows):
            y = j * pitch + 0.25
            _hcyl(s, wall_x + 0.6, y, zc, 0.35, 0.24, RED)   # contact band
            _hcyl(s, wall_x + 0.95, y, zc, 4.6, 0.2, WHITE)  # capacitor
    kw = dict(size=8.2)
    s.label("staircase bit-line", anchor=(wall_x - 5.0, 2.5, 2 * dz + 0.3),
            via=(0.20, 0.30), position=(0.03, 0.30), **kw)
    s.label("transistors", anchor=(wall_x + 0.3, 2.5, levels * dz),
            via=(0.44, 0.10), position=(0.44, 0.06), justify="center", **kw)
    s.label("size of storage capacitor",
            anchor=(wall_x + 3.2, 4.4, 9 * dz + 0.33),
            via=(0.80, 0.14), position=(0.97, 0.14), justify="right", **kw)
    return s


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.6))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.90, bottom=0.02,
                        wspace=0.04)
    panels = [
        (vertical_capacitors(), "(a) vertical capacitors on a bit-line array",
         dict(zoom=0.92, azimuth=-118, elevation=6)),
        (staircase_capacitors(), "(b) horizontal capacitors, staircase bit-line",
         dict(zoom=1.05, azimuth=-118, elevation=6)),
    ]
    for ax, (scene, title, cam) in zip(axes, panels):
        img = scene.render_array(print_width_in=3.1, aspect=1.05, **cam)
        ax.imshow(img)
        ax.set_axis_off()
        ax.set_title(title, fontsize=8.3, color=C_SLATE, weight="bold",
                     loc="left", pad=4)
    fig.text(0.5, 0.965, "3D DRAM capacitor schematics (role colors: bit "
             "line red, transistor green, capacitor white)",
             fontsize=7.4, color=C_GREY, ha="center")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "dram3d_capacitor_schematics"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
