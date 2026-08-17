"""fig_chiplet_package.py -- chiplet CPU package authored from a reference image.

A modular server-CPU package: a PCB substrate with a raised plateau, a 2 x 2
quad of compute tiles, small I/O tiles around it, three 3D-stacked customer
chiplet towers, die-to-die (D2D) bridges in the tile gaps, and peripheral
pads. The composition, viewpoint and callout set follow a supplied
manufacturer illustration of a customizable chiplet Xeon-class package
(compute tiles, customer chiplets, D2D interconnect, 3D packaging); the
geometry, dimensions and colors are new. Provenance is recorded in
``examples/REFERENCES.md``; the reference image is not redistributed.

Material language (packaging view, as in fig_hbm_labeled.py): the substrate
is PCB green, silicon parts take the neutral die grey with the logic tiles
one shade darker, D2D bridges are Cu, peripheral pads are Sn. Color means
material, not circuit role; the callouts carry the roles.

Outputs: ../docs/figures/chiplet_package.png and chiplet_package.pdf
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from semi_structures.solid import Scene
from semi_structures.style import PLOT_STYLE, doped

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

DIE = "substrate"                 # I/O tiles, chiplet stacks: neutral die grey
LOGIC = doped("substrate", 0.14)  # compute tiles: one shade darker

# ---- layout (model units) ---------------------------------------------------
SUB = (24.0, 17.0, 0.9)           # PCB substrate
PLATEAU = ((1.6, 1.2, 0.9), (20.8, 15.0, 0.35))
Z = 1.25                          # plateau top: everything sits here
TILE, GAP = 4.0, 0.35             # compute tile edge and gap
QX, QY = 13.2, 8.6                # compute quad centre
Q_X0 = (QX - GAP / 2 - TILE, QX + GAP / 2)
Q_Y0 = (QY - GAP / 2 - TILE, QY + GAP / 2)


def build():
    s = Scene()

    # Substrate and raised plateau.
    s.box((0, 0, 0), SUB, "PCB")
    s.box(*PLATEAU, "PCB")

    # 2 x 2 compute quad.
    for x0 in Q_X0:
        for y0 in Q_Y0:
            s.box((x0, y0, Z), (TILE, TILE, 0.45), LOGIC)

    # I/O tiles: 2 x 2 groups left and right, pairs above and below.
    io_h = (TILE * 2 + GAP - 0.3) / 2
    for x0 in (Q_X0[0] - 0.25 - 1.75, Q_X0[0] - 0.25 - 1.75 - 0.2 - 1.75):
        for y0 in (Q_Y0[0], Q_Y0[0] + io_h + 0.3):
            s.box((x0, y0, Z), (1.75, io_h, 0.4), DIE)
    for x0 in (Q_X0[1] + TILE + 0.25, Q_X0[1] + TILE + 0.25 + 1.75 + 0.2):
        for y0 in (Q_Y0[0], Q_Y0[0] + io_h + 0.3):
            s.box((x0, y0, Z), (1.75, io_h, 0.4), DIE)
    for x0 in Q_X0:                                   # top pair
        s.box((x0, Q_Y0[1] + TILE + 0.3, Z), (TILE, 1.4, 0.4), DIE)
    for x0 in (Q_X0[1], Q_X0[1] + 2.1):               # bottom pair, right side
        s.box((x0, Q_Y0[0] - 0.3 - 1.4, Z), (1.9, 1.4, 0.4), DIE)

    # Three 3D-stacked customer chiplet towers, in a diagonal row in front
    # of the left I/O group: five levels of a 2 x 2 sub-tile array with thin
    # Cu bond layers between levels.
    towers = [(2.9, 4.2), (5.2, 2.9), (7.5, 1.6)]
    sub, pitch, level_h, bond_h = 0.85, 1.05, 0.30, 0.06
    for tx, ty in towers:
        z = Z
        for level in range(5):
            if level:
                s.box((tx, ty, z), (sub + pitch, sub + pitch, bond_h), "Cu")
                z += bond_h
            for dx in (0.0, pitch):
                for dy in (0.0, pitch):
                    s.box((tx + dx, ty + dy, z), (sub, sub, level_h), DIE)
            z += level_h

    # D2D bridges: Cu pads in the gaps between tiles.
    gx = Q_X0[0] + TILE                               # vertical gap x
    for y in (Q_Y0[0] + 0.9, Q_Y0[0] + 2.4, Q_Y0[1] + 0.9, Q_Y0[1] + 2.4):
        s.box((gx + 0.05, y, Z), (GAP - 0.1, 0.8, 0.2), "Cu")
    gy = Q_Y0[0] + TILE                               # horizontal gap y
    for x in (Q_X0[0] + 0.9, Q_X0[0] + 2.4, Q_X0[1] + 0.9, Q_X0[1] + 2.4):
        s.box((x, gy + 0.05, Z), (0.8, GAP - 0.1, 0.2), "Cu")
    top_gap_y = Q_Y0[1] + TILE + 0.05                 # quad -> top I/O pair
    for x in (Q_X0[0] + 1.6, Q_X0[1] + 1.6):
        s.box((x, top_gap_y, Z), (0.8, 0.2, 0.2), "Cu")
    for x0, dx in ((Q_X0[0] - 0.225, 0.2), (Q_X0[1] + TILE + 0.05, 0.2)):
        for y in (Q_Y0[0] + 1.6, Q_Y0[1] + 1.6):     # quad <-> side groups
            s.box((x0, y, Z), (dx, 0.8, 0.2), "Cu")

    # Peripheral pads on the substrate margins (front and back rows).
    for row_y in (0.25, 0.7):
        for i in range(22):
            s.box((1.5 + i * 0.95, row_y, 0.9), (0.35, 0.3, 0.1), "Sn")
    for i in range(22):
        s.box((1.5 + i * 0.95, 16.45, 0.9), (0.35, 0.3, 0.1), "Sn")

    # ---- callouts (points at the print width declared in render) ---------
    # Screen positions assume the camera in main(): +x,-y three-quarter view,
    # towers front-left; labels live in the white margins either side.
    s.text2d("Chiplet CPU package\nsolid-backend testcase",
             position="upper_left", size=10.0)
    tx, ty = towers[0]
    tower_top = Z + 5 * level_h + 4 * bond_h
    s.label("customer chiplets\n(3D-stacked)",
            anchor=(tx + 0.95, ty + 0.95, tower_top),
            via=(0.17, 0.66), position=(0.03, 0.66), size=8.2)
    s.label("package substrate (PCB)", anchor=(0.9, 9.0, 0.9),
            via=(0.14, 0.30), position=(0.03, 0.30), size=8.2)
    s.label("peripheral pads (Sn)", anchor=(3.4, 0.4, 1.0),
            via=(0.20, 0.90), position=(0.03, 0.90), size=8.2)
    s.label("die-to-die (D2D) bridges (Cu)",
            anchor=(gx + GAP / 2, Q_Y0[1] + 2.8, Z + 0.2),
            via=(0.74, 0.12), position=(0.97, 0.12), justify="right",
            size=8.2)
    s.label("compute tiles", anchor=(Q_X0[1] + 2.0, Q_Y0[1] + 2.0, Z + 0.45),
            via=(0.80, 0.36), position=(0.97, 0.36), justify="right",
            size=8.2)
    s.label("I/O tiles", anchor=(Q_X0[1] + TILE + 0.25 + 0.9,
                                 Q_Y0[0] + io_h / 2, Z + 0.4),
            via=(0.86, 0.62), position=(0.97, 0.62), justify="right",
            size=8.2)
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "chiplet_package.png"
    print_width, aspect = 6.3, 0.62
    # Camera from +x, -y (towers front-left, as in the reference), raised
    # towards a three-quarter top view.
    build().render(str(png), print_width_in=print_width, aspect=aspect,
                   zoom=1.22, azimuth=-120.0, elevation=10.0)

    # Full-bleed axes: the image prints at the width its text was sized for.
    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(print_width, print_width * aspect))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(mpimg.imread(png))
    ax.set_axis_off()
    fig.savefig(OUT / "chiplet_package.pdf")
    plt.close(fig)
    print(f"wrote {png} and {OUT / 'chiplet_package.pdf'}")


if __name__ == "__main__":
    main()
