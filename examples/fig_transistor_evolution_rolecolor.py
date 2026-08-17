"""fig_transistor_evolution_rolecolor.py -- the transistor line-up in role colors.

The planar / FinFET / GAAFET / CFET line-up colored the way the classic
evolution diagram is: color means CIRCUIT ROLE, not material -- gate green,
PMOS blue, NMOS red, well pink, isolation and substrate grey -- with a
PMOS/NMOS pair in every device. Rendered with the solid backend
(semi_structures.solid: true solids, PyVista parallel projection), so fins
and nanosheets emerge from opaque gates with correct occlusion. This is a
deliberate presentation override of the book's material palette (raw hex
fills are allowed by the renderers), kept as a separate example so the
material-colored figures remain the defaults. The reference diagram is not
redistributed; the geometry here is the package's own.

Outputs: ../docs/figures/transistor_evolution_rolecolor.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures.solid import Scene
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

# Role colors (after the reference diagram) -- not the material palette.
GATE = "#9CBF4A"      # green
PMOS = "#2A6BD6"      # blue
NMOS = "#D8262A"      # red
WELL = "#CF97A0"      # pink
ISO = "#C9CCCF"       # isolation (oxide), light grey
SUB = "#A9AEB3"       # substrate, grey
EDGE = "#8a949c"

PANEL_W_IN = 6.3 * 24.6 / 100.0      # printed width of one 3D panel


def _callouts(s, pmos_anchor, nmos_anchor, gate_anchor):
    kw = dict(size=7.2, line_width=0.5)
    s.label("PMOS", anchor=pmos_anchor, via=(0.16, 0.16),
            position=(0.03, 0.16), **kw)
    s.label("NMOS", anchor=nmos_anchor, via=(0.84, 0.16),
            position=(0.97, 0.16), justify="right", **kw)
    s.label("gate", anchor=gate_anchor, via=(0.50, 0.06),
            position=(0.50, 0.03), justify="center", **kw)


def planar_scene():
    """Shared gate across a PMOS (front) and an NMOS (back) half."""
    s = Scene()
    s.box((0, 0, 0), (10, 7, 1.5), SUB)
    s.box((0, 0, 1.5), (10, 7, 1.0), ISO)
    s.box((0.7, 0.5, 2.5), (8.6, 6.0, 0.55), WELL)
    for y0, dev in ((0.5, PMOS), (3.6, NMOS)):
        s.box((0.7, y0, 3.05), (2.4, 2.9, 1.15), dev)
        s.box((6.9, y0, 3.05), (2.4, 2.9, 1.15), dev)
    s.box((3.55, 0.5, 3.05), (2.9, 6.0, 1.7), GATE)
    _callouts(s, (1.9, 1.9, 4.2), (8.1, 5.0, 4.2), (5.0, 3.5, 4.75))
    return s


def finfet_scene():
    s = Scene()
    s.box((0, 0, 0), (10, 7, 1.5), SUB)
    s.box((0, 0, 1.5), (10, 7, 0.8), ISO)
    for y_fin, dev in ((1.5, PMOS), (4.3, NMOS)):
        s.box((0.6, y_fin, 2.3), (3.3, 1.1, 2.3), dev)      # S/D + channel
        s.box((3.9, y_fin, 2.3), (2.2, 1.1, 2.3), WELL)     # inside the gate
        s.box((6.1, y_fin, 2.3), (3.3, 1.1, 2.3), dev)
    s.box((3.9, 0.4, 2.3), (2.2, 6.2, 3.0), GATE)
    _callouts(s, (2.25, 2.05, 4.6), (7.75, 4.85, 4.6), (5.0, 3.5, 5.3))
    return s


def gaafet_scene():
    s = Scene()
    s.box((0.6, 0, 0), (8.8, 7, 1.5), SUB)
    s.box((0.6, 0, 1.5), (8.8, 7, 0.8), ISO)
    for y0, dev in ((1.0, PMOS), (4.2, NMOS)):
        for z_rib in (2.9, 4.0, 5.1):
            s.box((0.9, y0, z_rib), (3.0, 1.8, 0.5), dev)
            s.box((3.9, y0, z_rib), (2.2, 1.8, 0.5), WELL)
            s.box((6.1, y0, z_rib), (3.0, 1.8, 0.5), dev)
    s.box((3.9, 0.4, 2.3), (2.2, 6.2, 3.9), GATE)
    _callouts(s, (2.4, 1.9, 5.6), (7.6, 5.1, 5.6), (5.0, 3.5, 6.2))
    return s


def cfet_scene():
    """NMOS sheets stacked over PMOS sheets, one gate, one footprint."""
    s = Scene()
    s.box((1.6, 0, 0), (6.8, 7, 1.5), SUB)
    s.box((1.6, 0, 1.5), (6.8, 7, 0.8), ISO)
    for z_rib, dev in [(2.6, PMOS), (3.4, PMOS), (4.2, PMOS),
                       (5.4, NMOS), (6.2, NMOS), (7.0, NMOS)]:
        s.box((2.0, 2.2, z_rib), (2.0, 2.6, 0.45), dev)
        s.box((4.0, 2.2, z_rib), (2.0, 2.6, 0.45), WELL)
        s.box((6.0, 2.2, z_rib), (2.0, 2.6, 0.45), dev)
    s.box((4.0, 1.5, 2.3), (2.0, 4.0, 5.6), GATE)
    kw = dict(size=7.2, line_width=0.5)
    s.label("PMOS", anchor=(7.0, 3.5, 3.6), via=(0.84, 0.72),
            position=(0.97, 0.72), justify="right", **kw)
    s.label("NMOS", anchor=(7.0, 3.5, 6.4), via=(0.84, 0.16),
            position=(0.97, 0.16), justify="right", **kw)
    s.label("gate", anchor=(5.0, 3.5, 7.9), via=(0.30, 0.06),
            position=(0.30, 0.03), justify="center", **kw)
    return s


def cross_section(ax, cx, kind):
    def rect(x, y, w, h, color, label=None):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color,
                                   edgecolor=EDGE, lw=0.5))
        if label:
            ax.text(x + w / 2, y + h / 2, label, fontsize=7.0,
                    color=C_SLATE, ha="center", va="center")

    if kind == "planar":
        # Cut along the channel, not across it. The across-channel cut of a
        # planar device is only a stack of layers: no source, no drain, no
        # channel, and nothing that shows why the gate controls one face.
        # This is the same content as the 3D panel above, PMOS beside NMOS.
        rect(cx - 8, 11.0, 16, 2.4, SUB, "substrate")
        rect(cx - 8, 13.4, 16, 4.0, WELL)
        ax.text(cx, 14.2, "well", fontsize=7.0, color=C_SLATE,
                ha="center", va="center")
        for x0 in (cx - 8.0, cx - 0.9, cx + 7.1):        # isolation
            rect(x0, 15.0, 1.8 if abs(x0 - cx) < 1 else 0.9, 2.4, ISO)
        for dcx, dev in ((cx - 4.0, PMOS), (cx + 4.0, NMOS)):
            rect(dcx - 3.1, 15.2, 2.3, 2.2, dev)         # source
            rect(dcx + 0.8, 15.2, 2.3, 2.2, dev)         # drain
            rect(dcx - 1.6, 17.4, 3.2, 0.35, ISO)        # gate oxide
            rect(dcx - 1.6, 17.75, 3.2, 3.2, GATE)       # gate
            ax.text(dcx, 21.4, "gate", fontsize=7.0, color=C_SLATE,
                    ha="center")
        note = "gate controls one face"
    elif kind == "fin":
        rect(cx - 8, 11.0, 16, 2.6, SUB, "substrate")
        rect(cx - 6, 13.6, 12, 12.6, GATE)
        ax.text(cx, 24.6, "gate", fontsize=7.0, color=C_SLATE, ha="center")
        rect(cx - 3.4, 13.6, 2.2, 9.2, PMOS)
        rect(cx + 1.2, 13.6, 2.2, 9.2, NMOS)
        note = "gate wraps 3 sides"
    elif kind == "gaa":
        rect(cx - 6, 11.0, 12, 2.6, SUB, "substrate")
        rect(cx - 4.4, 13.6, 8.8, 14.2, GATE)
        ax.text(cx, 25.6, "gate", fontsize=7.0, color=C_SLATE, ha="center")
        for y0 in (15.2, 18.6, 22.0):
            rect(cx - 3.9, y0, 3.2, 2.0, PMOS)
            rect(cx + 0.7, y0, 3.2, 2.0, NMOS)
        note = "gate wraps 4 sides"
    else:
        rect(cx - 5, 11.0, 10, 2.2, SUB, "substrate")
        rect(cx - 3.6, 13.2, 7.2, 20.4, GATE)
        ax.text(cx, 31.2, "gate", fontsize=7.0, color=C_SLATE, ha="center")
        for y0 in (14.6, 17.2, 19.8):
            rect(cx - 2.3, y0, 4.6, 1.6, PMOS)
        for y0 in (23.6, 26.2, 28.8):
            rect(cx - 2.3, y0, 4.6, 1.6, NMOS)
        ax.text(cx + 4.4, 17.8, "p", fontsize=7.0, color=C_SLATE)
        ax.text(cx + 4.4, 26.8, "n", fontsize=7.0, color=C_SLATE)
        note = "two devices, one footprint"
    ax.text(cx, 8.0, note, fontsize=7.0, color=C_SLATE, ha="center")


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=(6.3, 5.55))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 88)
    ax.set_aspect("equal")
    ax.set_axis_off()

    panels = [("Planar", "(pre 2011)", 12.5, "planar", planar_scene, 1.3),
              ("FinFET", "(2011$-$2023)", 37.5, "fin", finfet_scene, 1.3),
              ("GAAFET", "(2023$-$)", 62.5, "gaa", gaafet_scene, 1.3),
              ("CFET", "(2032?)", 87.5, "cfet", cfet_scene, 1.15)]
    for name, years, cx, kind, builder, zoom in panels:
        ax.text(cx, 84.5, name, fontsize=9.0, color=C_SLATE, ha="center",
                weight="bold")
        ax.text(cx, 81.0, years, fontsize=7.2, color=C_GREY, ha="center")
        # each panel prints PANEL_W_IN wide: text sizes are points there
        img = builder().render_array(print_width_in=PANEL_W_IN, aspect=0.90,
                                     zoom=zoom, azimuth=-30.0,
                                     elevation=-16.0)
        h = 24.6 * img.shape[0] / img.shape[1]
        ax.imshow(img, extent=(cx - 12.3, cx + 12.3, 72.5 - h, 72.5),
                  zorder=3)
        cross_section(ax, cx, kind)

    for y, lab in [(56.0, "3D view"), (18.0, "cross-\nsection")]:
        ax.text(1.2, y, lab, fontsize=7.6, color=C_SLATE, ha="center",
                va="center", rotation=90)
    ax.plot([6.5, 99], [41.0, 41.0], color=C_GREY, lw=0.7, ls=(0, (4, 3)))
    ax.text(50, 1.2, "color = circuit role (after the classic evolution "
            "diagram): gate green, PMOS blue, NMOS red, well pink, "
            "isolation (oxide) and substrate grey; solid backend",
            fontsize=7.0, color=C_GREY, ha="center")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "transistor_evolution_rolecolor"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
