"""fig_dram3d_reference_colors.py -- 3D DRAM array in a presentation color scheme.

A horizontal-capacitor 3D DRAM archetype drawn the way a vendor concept
rendering presents it: dark navy background, light-grey capacitor plates
stacked in layers on both sides of a central transistor spine, dark
dielectric between plates, blue word lines / transistors, teal channel
pillars and a teal vertical bit line, white callouts. Color here is
PRESENTATION and ROLE (after the supplied NEO Semiconductor 3D X-DRAM
concept image), not the book's material palette; the geometry is the
package's own schematic, not a reproduction, and the reference image is not
redistributed (provenance in examples/REFERENCES.md).

Outputs: ../docs/figures/dram3d_reference_colors.png and .pdf
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from semi_structures.solid import Scene
from semi_structures.style import PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

# Presentation colors (after the reference), not the material palette.
BG = "#0E1B3D"          # dark navy background
PLATE = "#C9CBCF"       # capacitor plates, light grey
DIEL = "#243766"        # dielectric between plates, dark blue
GOX = "#2F4A8F"         # gate oxide, mid-dark blue
TRANS = "#3D6BD8"       # transistors / word lines, blue
CHAN = "#3FD1B4"        # channel pillars and bit line, teal
TEXT = "#F4F6F8"
LEADER = "#DDE3EE"
EDGE = "#3B4B72"

LAYERS, PITCH, T_PLATE = 8, 0.56, 0.32       # layer count, pitch, plate thickness
ROWS, ROW_PITCH, ROW_W = 5, 1.45, 1.15       # plate rows along y
L_X = (0.0, 5.0)                             # left block x extent
R_X = (7.0, 12.0)                            # right block x extent
SPINE = (5.0, 7.0)                           # transistor spine between blocks


def build():
    s = Scene()
    top = 0.0
    for k in range(LAYERS):
        z = k * PITCH
        top = z + T_PLATE
        for j in range(ROWS):
            y0 = j * ROW_PITCH
            for x0, x1 in (L_X, R_X):
                s.box((x0, y0, z), (x1 - x0, ROW_W, T_PLATE), PLATE)
                if k < LAYERS - 1:                       # dielectric spacer
                    s.box((x0, y0, top), (x1 - x0, ROW_W, PITCH - T_PLATE),
                          DIEL)
        # transistor bar across the spine, with thin gate-oxide skins where
        # it meets the plates
        s.box((SPINE[0] + 0.3, 0.0, z), (SPINE[1] - SPINE[0] - 0.6,
                                         ROWS * ROW_PITCH - 0.3, T_PLATE),
              TRANS)
        for x0 in (SPINE[0], SPINE[1] - 0.3):
            s.box((x0, 0.0, z), (0.3, ROWS * ROW_PITCH - 0.3, T_PLATE), GOX)
        if k < LAYERS - 1:
            s.box((SPINE[0], 0.0, top), (SPINE[1] - SPINE[0],
                                         ROWS * ROW_PITCH - 0.3,
                                         PITCH - T_PLATE), DIEL)

    # word lines on top of the spine, and channel pillars between them
    for x0 in (SPINE[0] + 0.15, SPINE[1] - 0.6):
        s.box((x0, -0.2, top), (0.45, ROWS * ROW_PITCH + 0.1, 0.28), TRANS)
    xc = 0.5 * (SPINE[0] + SPINE[1])
    for j in range(ROWS):
        s.cylinder((xc, j * ROW_PITCH + ROW_W / 2), top, 0.17, 0.85, CHAN)
    # vertical bit line at the front of the spine
    s.cylinder((xc, -0.55), 0.0, 0.2, top + 0.7, CHAN)

    # ---- callouts (white on the dark background) --------------------------
    s.text2d("3D DRAM", position="upper_left", size=12.0, bold=True,
             color=TEXT)
    y_mid = ROWS * ROW_PITCH / 2
    kw = dict(size=8.2, color=TEXT, line_color=LEADER)
    s.label("word line", anchor=(SPINE[0] + 0.35, y_mid, top + 0.28),
            via=(0.20, 0.30), position=(0.03, 0.30), **kw)
    s.label("channel", anchor=(xc, 2 * ROW_PITCH + ROW_W / 2, top + 0.85),
            via=(0.20, 0.40), position=(0.03, 0.40), **kw)
    s.label("gate oxide (GOX)", anchor=(SPINE[0] + 0.15, 0.6, 3 * PITCH + 0.16),
            via=(0.20, 0.58), position=(0.03, 0.58), **kw)
    s.label("dielectric", anchor=(2.5, 0.6, 2 * PITCH + T_PLATE + 0.1),
            via=(0.20, 0.78), position=(0.03, 0.78), **kw)
    s.label("bit line", anchor=(xc, -0.55, 0.9),
            via=(0.20, 0.90), position=(0.03, 0.90), **kw)
    s.label("transistor", anchor=(xc, 3.5 * ROW_PITCH, top),
            via=(0.62, 0.15), position=(0.62, 0.10), justify="center", **kw)
    s.label("capacitor", anchor=(R_X[0] + 3.5, 3.6 * ROW_PITCH, top),
            via=(0.82, 0.15), position=(0.82, 0.10), justify="center", **kw)
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "dram3d_reference_colors.png"
    print_width, aspect = 6.3, 0.62
    build().render(str(png), print_width_in=print_width, aspect=aspect,
                   zoom=1.25, azimuth=-118.0, elevation=8.0,
                   background=BG, edge_color=EDGE)

    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(print_width, print_width * aspect))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(mpimg.imread(png))
    ax.set_axis_off()
    fig.savefig(OUT / "dram3d_reference_colors.pdf")
    plt.close(fig)
    print(f"wrote {png} and {OUT / 'dram3d_reference_colors.pdf'}")


if __name__ == "__main__":
    main()
