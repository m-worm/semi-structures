"""fig_litho_flow_3d.py -- the photolithography flow as solid 3D states.

The same six ``Wafer`` states as fig_litho_flow.py, drawn by the true-solid
backend instead of the 2D section renderer: deposition, resist coating,
exposure through a photomask, development, film etch and resist removal.
Seeing the flow in 3D shows what a section cannot, namely that the openings
are trenches across the die rather than isolated holes.

The photomask and the exposure light are annotations rather than process
steps. The light is drawn with ``Scene.cone()``, tapering from the mask
opening down to the resist, in the reserved beam color.

Outputs: ../docs/figures/litho_flow_3d.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Rectangle, Wafer
from semi_structures.style import (
    C_EVANESCENT, C_GREY, C_SLATE, MATERIAL, PLOT_STYLE, mix,
)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

W, D = 10.0, 6.0                       # die footprint
T_SUB, T_FILM, T_RESIST = 1.5, 0.5, 1.0
OPENINGS = [(0.6, 2.6), (4.2, 5.8), (7.4, 9.4)]     # x ranges patterned
RESIST_EXPOSED = mix(MATERIAL["resist"][0], "#FFFFFF", 0.5)

CAMERA = dict(azimuth=-30.0, elevation=20.0, zoom=1.02)


def state(step):
    """The wafer after litho step ``step`` (1..6)."""
    w = Wafer(size=(W, D), substrate="Si", thickness=T_SUB, name="wafer")
    w.add_layer("SiO2", T_FILM, name="oxide")
    if step >= 2:
        w.add_layer("resist", T_RESIST, name="resist")
    if step >= 3:                                    # exposure
        for x0, x1 in OPENINGS:
            w.implant(Rectangle.from_corner(x0, 0.0, x1 - x0, D),
                      RESIST_EXPOSED, depth=T_RESIST, name="exposed")
    if step >= 4:                                    # development
        for x0, x1 in OPENINGS:
            w.etch(Rectangle.from_corner(x0, 0.0, x1 - x0, D),
                   depth=T_RESIST, name="developed")
    if step >= 5:                                    # film etch
        for x0, x1 in OPENINGS:
            w.etch(Rectangle.from_corner(x0, 0.0, x1 - x0, D),
                   stop_on="wafer", name="etched")
    if step >= 6:                                    # resist strip
        w.strip("resist")
    return w


def annotate(scene, step):
    """Photomask and light for the exposure panel, ions for the etch."""
    if step == 3:
        z_mask = T_SUB + T_FILM + T_RESIST + 2.6
        scene.box((-0.4, -0.4, z_mask), (W + 0.8, D + 0.8, 0.35),
                  "substrate", opacity=0.55)
        for a, b in ((2.6, 4.2), (5.8, 7.4)):        # chrome between openings
            scene.box((a, -0.4, z_mask + 0.35), (b - a, D + 0.8, 0.18), "W")
        # light: one cone per opening, converging from the mask onto the
        # resist, so the taper reads as a beam
        top = T_SUB + T_FILM + T_RESIST
        for x0, x1 in OPENINGS:
            scene.cone(((x0 + x1) / 2, D / 2), top, z_mask - top,
                       C_EVANESCENT, r_bottom=0.30 * (x1 - x0),
                       r_top=0.50 * (x1 - x0), opacity=0.42)
    elif step == 5:
        z_top = T_SUB + T_FILM + T_RESIST
        for x0, x1 in OPENINGS:                      # ions, narrowing down
            scene.cone(((x0 + x1) / 2, D / 2), z_top + 0.15, 3.0, C_GREY,
                       r_bottom=0.12 * (x1 - x0), r_top=0.34 * (x1 - x0),
                       opacity=0.34)


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    captions = ["1  deposition", "2  resist coating", "3  exposure",
                "4  development", "5  film etch", "6  resist removal"]

    # An explicit vertical budget in inches, so nothing can overlap.
    panel_w, aspect = 6.3 / 3, 0.78
    panel_h = panel_w * aspect
    header, caption_h, footer = 0.30, 0.28, 0.26
    total = header + 2 * (panel_h + caption_h) + footer
    fig = plt.figure(figsize=(6.3, total))

    for index, caption in enumerate(captions):
        row, col = divmod(index, 3)
        wafer = state(index + 1)
        scene = wafer.model(backend="solid")
        annotate(scene, index + 1)
        image = scene.render_array(print_width_in=panel_w, aspect=aspect,
                                   transparent=True, **CAMERA)
        bottom = (footer + (1 - row) * (panel_h + caption_h) + caption_h)
        axes = fig.add_axes([col / 3, bottom / total, 1 / 3, panel_h / total])
        axes.imshow(image)
        axes.set_axis_off()
        axes.text(0.5, -0.03, caption, transform=axes.transAxes, fontsize=8.0,
                  color=C_SLATE, ha="center", va="top", weight="bold")

    fig.text(0.5, 1 - 0.06 / total,
             "Photolithography in six solid states: the openings are trenches "
             "across the die, not isolated holes",
             fontsize=7.6, color=C_GREY, ha="center", va="top")
    fig.text(0.5, 0.07 / total,
             "Mask, light and ions are annotations. The beams are "
             "Scene.cone() in the reserved beam color.",
             fontsize=7.0, color=C_GREY, ha="center", va="bottom")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "litho_flow_3d"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
