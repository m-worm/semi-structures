"""fig_hbm_labeled.py -- callout-label testcase for the solid backend.

An HBM package inspired by the supplied reference: package substrate,
Sn solder-ball array, silicon interposer, GPU die, and an eight-die HBM tower.
Every callout is created by Scene.label(), so the leader anchors live in the
same 3D coordinate system as the solid geometry and remain attached when the
camera changes.

Reference-image provenance: the supplied screenshot is from Hanwha's
``Powering AI: Advanced semiconductor manufacturing solutions`` feature:
https://www.hanwha.com/newsroom/news/feature-stories/powering-ai-semiconductor-manufacturing-solutions.do
This script is an independent schematic, not a reproduction of that image.

Outputs: ../docs/figures/hbm_labeled.png and hbm_labeled.pdf
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from semi_structures.solid import C_SLATE, Scene
from semi_structures.style import PLOT_STYLE, doped

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"
# The palette default leader grey reads faintly against grey dies, so the
# leaders here take the text color instead.
LEADER = C_SLATE
# Packaging view: dies and interposer take the palette's light-grey neutral
# ("substrate", #DCE0E4) rather than the Si blue, so the package materials
# (PCB green, Sn, Cu) carry the color and the silicon parts read as parts.
DIE = "substrate"                 # memory dies and interposer
LOGIC = doped("substrate", 0.14)  # logic dies: one shade darker


def build():
    s = Scene()

    # Package substrate, Sn solder-ball array, and silicon interposer.
    s.box((0, 0, 0), (16, 11, 0.9), "PCB")     # organic laminate: PCB green
    s.sphere_array((2.0, 13.8), (1.9, 9.3), 1.55,
                   z=1.42, r=0.45, material="Sn")
    s.box((1.2, 1.2, 1.82), (13.6, 8.6, 0.55), DIE)     # Si interposer

    # Cu microbumps under the GPU and HBM logic die.
    s.sphere_array((8.5, 13.9), (2.6, 8.6), 0.75,
                   z=2.49, r=0.13, material="Cu")
    s.sphere_array((2.6, 6.2), (2.6, 8.6), 0.75,
                   z=2.49, r=0.13, material="Cu")

    # GPU and HBM logic die.
    s.box((7.9, 2.3, 2.62), (6.2, 6.4, 0.8), LOGIC)     # GPU die
    s.box((2.0, 2.3, 2.62), (4.6, 6.4, 0.55), LOGIC)    # HBM logic die

    # Eight DRAM dies separated by thin Cu bonding layers.
    z = 3.17
    for _ in range(8):
        s.box((2.35, 2.65, z), (3.9, 5.7, 0.10), "Cu")
        s.box((2.0, 2.3, z + 0.10), (4.6, 6.4, 0.34), DIE)
        z += 0.44

    s.text2d("High-bandwidth memory\nsolid-backend label testcase",
             position="upper_left", size=10.0)

    # Stick-and-ball callouts. Each anchor is a 3D feature coordinate that the
    # camera projects, so it must sit on a face the camera can actually see:
    # +x, +y and +z all run toward the viewer here, which makes the x-max,
    # y-max and top faces the visible ones. Positions and elbow points are
    # normalized screen coordinates for a stable publication layout, and sizes
    # are points at the 6.3 in print width declared in render().
    call = dict(size=8.2, marker="dot", line_color=LEADER, line_width=0.8)
    right = dict(justify="right", **call)

    # Right column: down the tower, then the bump row that clears the GPU
    # edge at y = 8.6, then the board rim.
    s.label("HBM DRAM dies (x8)", anchor=(4.3, 8.7, 5.20),
            via=(0.76, 0.26), position=(0.95, 0.20), **right)
    s.label("HBM logic die", anchor=(4.3, 8.7, 2.895),
            via=(0.76, 0.42), position=(0.95, 0.38), **right)
    s.label("Cu microbumps", anchor=(10.75, 8.6, 2.49),
            via=(0.76, 0.60), position=(0.95, 0.56), **right)
    # The longest caption needs its elbow further left, clear of the text box.
    s.label("package substrate (PCB)", anchor=(8.0, 11.0, 0.45),
            via=(0.70, 0.72), position=(0.95, 0.72), **right)

    # Left column: the GPU top face, then the two levels below it.
    s.label("GPU die", anchor=(11.0, 5.5, 3.42),
            via=(0.25, 0.50), position=(0.05, 0.47), **call)
    s.label("Si interposer", anchor=(14.8, 1.6, 2.09),
            via=(0.25, 0.64), position=(0.05, 0.62), **call)
    s.label("Sn solder-ball array", anchor=(13.10, 1.96, 1.03),
            via=(0.25, 0.80), position=(0.05, 0.78), **call)
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "hbm_labeled.png"
    print_width, aspect = 6.3, 0.71
    build().render(str(png), print_width_in=print_width, aspect=aspect,
                   zoom=0.88, azimuth=-30.0, elevation=-16.0)

    # PDF wrapper: full-bleed axes so the image prints at exactly the width
    # the text sizes were computed for.
    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(print_width, print_width * aspect))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(mpimg.imread(png))
    ax.set_axis_off()
    fig.savefig(OUT / "hbm_labeled.pdf")
    plt.close(fig)
    print(f"wrote {png} and {OUT / 'hbm_labeled.pdf'}")


if __name__ == "__main__":
    main()
