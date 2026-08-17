"""fig_backside_power_delivery.py -- nTSV / buried-power-rail testcase.

Inspired by the supplied signal-versus-power references and grounded in:

* Intel Foundry, ``Cutting-edge Process Technologies for Data Center``,
  Figure 4 (PowerVia tower rendering),
  https://www.intel.com/content/www/us/en/foundry/library/advanced-process-technologies-for-data-center.html
* Aminext, ``What is Backside Power Delivery (BSP)?``, nTSV diagram,
  https://www.aminext.blog/en/post/backside-power-delivery-bsp-explained-1

* D. Prasad et al., IEDM (2019),
  https://doi.org/10.1109/IEDM19573.2019.8993617
* A. Veloso et al., VLSI Technology and Circuits (2022),
  https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830177
  and IEEE Trans. Electron Devices 69, 7173--7179 (2022),
  https://doi.org/10.1109/TED.2022.3205561

The illustration is schematic: backside Cu power metals connect through W
nano-TSVs to buried power rails below the transistor tier, while frontside Cu
signal layers remain above it.  It demonstrates solid boxes and cylinders,
transparency, repeated geometry, fixed titles, and 3D-anchored labels.
It is an independent schematic rather than a reproduction of either supplied
reference image.

Outputs: ../docs/figures/backside_power_delivery.png and .pdf
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


def build():
    scene = Scene()

    # Backside power metal: intentionally wider and thicker than signal lines.
    for y in (0.8, 3.2, 5.6, 8.0):
        scene.box((0.4, y, 0.0), (13.2, 0.85, 0.38), "Cu")
    scene.box((0.0, 0.0, 0.38), (14.0, 10.0, 0.28), "SiO2")

    # Extremely thinned Si body.  Opacity exposes the nano-TSVs.
    scene.box((0.0, 0.0, 0.66), (14.0, 10.0, 2.55), "Si", opacity=0.52)

    # nTSVs land on buried W rails close to the active device layer.
    for y in (1.25, 5.95):
        scene.box((0.8, y, 2.92), (12.4, 0.52, 0.42), "W")
        for x in (2.0, 5.2, 8.4, 11.6):
            scene.cylinder((x, y + 0.26), 0.35, 0.22, 2.75, "W")

    # A compact FinFET-like transistor tier between the two routing domains.
    for x in (1.5, 4.2, 6.9, 9.6):
        scene.box((x, 2.25, 3.18), (1.35, 5.0, 0.38), doped("Si", 0.20))
    for y in (2.55, 4.25, 5.95):
        scene.box((0.9, y, 3.10), (11.9, 0.58, 0.92), "TiN")

    # Frontside dielectric and signal metallization.
    scene.box((0.25, 0.25, 3.55), (13.5, 9.5, 2.55), "SiO2", opacity=0.24)
    for level, z in enumerate((3.95, 4.65, 5.35)):
        if level % 2 == 0:
            for y in (1.0, 2.65, 4.30, 5.95, 7.60):
                scene.box((0.65, y, z), (12.7, 0.35, 0.24), "Cu")
        else:
            for x in (1.1, 3.45, 5.80, 8.15, 10.50, 12.85):
                scene.box((x, 0.65, z), (0.35, 8.7, 0.24), "Cu")

    scene.text2d("Backside power delivery\nsolid-backend feature testcase",
                 position="upper_left", size=10.0)
    # Stick-and-ball callouts. Leaders take the text color: the palette
    # default grey reads faintly against the grey metals here.
    call = dict(size=8.2, marker="dot", line_color=C_SLATE, line_width=0.8)
    right = dict(justify="right", **call)
    scene.label("frontside signal layers", anchor=(12.8, 7.6, 5.58),
                via=(0.71, 0.18), position=(0.96, 0.14), **right)
    scene.label("transistor tier", anchor=(11.5, 6.53, 3.50),
                via=(0.77, 0.40), position=(0.96, 0.40), **right)
    scene.label("buried power rail (W)", anchor=(12.8, 6.2, 3.16),
                via=(0.73, 0.57), position=(0.96, 0.57), **right)
    scene.label("nTSV (W)", anchor=(11.93, 1.51, 1.65),
                via=(0.24, 0.38), position=(0.05, 0.38), **call)
    scene.label("backside power metals", anchor=(13.6, 0.95, 0.19),
                via=(0.25, 0.76), position=(0.05, 0.76), **call)
    # clear of both nTSV rows (y = 1.51 and 6.21), which sit just behind
    # this face and would otherwise take the dot
    scene.label("thinned Si", anchor=(14.0, 3.5, 1.30),
                via=(0.23, 0.58), position=(0.05, 0.58), **call)
    return scene


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "backside_power_delivery.png"
    print_width, aspect = 6.3, 0.73
    build().render(str(png), print_width_in=print_width, aspect=aspect,
                   zoom=0.92, azimuth=-30.0, elevation=-18.0)

    # Full-bleed axes: the image prints at the width its text was sized for.
    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(print_width, print_width * aspect))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(mpimg.imread(png))
    ax.set_axis_off()
    fig.savefig(OUT / "backside_power_delivery.pdf")
    plt.close(fig)
    print(f"wrote {png} and {OUT / 'backside_power_delivery.pdf'}")


if __name__ == "__main__":
    main()
