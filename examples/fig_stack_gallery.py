"""fig_stack_gallery.py -- the material palette on real-world stacks.

Six representative structures from semiconductor X-ray metrology, drawn
entirely from semi_structures.style.MATERIAL with alloy fills computed by
alloy_color(). Doubles as the palette's stress test: adjacent same-family
layers (SiO2/Si3N4 in the ON stack), Vegard-shaded alloys (Si0.7Ge0.3,
Al0.25Ga0.75N), and heavy/light rhythm (W/Si mirror). Authored at print
width (6.3 in) so point sizes are page sizes.

Outputs: ../docs/figures/stack_gallery.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

from semi_structures.style import (
    C_GREY, C_SLATE, MATERIAL, PLOT_STYLE, PRETTY, alloy_color, alpha_for,
)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

EDGE = "#aab1b7"
SIGE30 = alloy_color("Si", "Ge", 0.30)
ALGAN25 = alloy_color("AlN", "GaN", 0.25)


def fill(name):
    """(rgba) fill for a material name or raw hex; the transparent crystals
    keep their palette alpha so a SiC wafer reads as a clear substrate."""
    color = MATERIAL[name][0] if name in MATERIAL else name
    return to_rgba(color, alpha_for(name))


def label_of(name):
    return PRETTY.get(name, name).replace("\n", " ")


def draw_stack(ax, x0, w, base_y, layers, title):
    """layers: (material or hex, inside label or None, h, right label)."""
    y = base_y
    bounds = []
    for mat, inside, h, right in layers:
        ax.add_patch(plt.Rectangle((x0, y), w, h, facecolor=fill(mat),
                                   edgecolor=EDGE, lw=0.5))
        text = inside if inside is not None else label_of(mat)
        if h >= 2.6 and text:
            ax.text(x0 + w / 2, y + h / 2, text, fontsize=7.0,
                    color=C_SLATE, ha="center", va="center")
        if right:
            ax.text(x0 + w + 0.9, y + h / 2, right, fontsize=7.0,
                    color=C_GREY, ha="left", va="center")
        bounds.append((y, y + h))
        y += h
    ax.text(x0 + w / 2, base_y - 2.6, title, fontsize=7.5, color=C_SLATE,
            ha="center", va="top")
    return bounds


def bracket(ax, x, y0, y1, label):
    ax.plot([x, x + 1.0, x + 1.0, x], [y0, y0, y1, y1], color=C_SLATE,
            lw=0.7)
    ax.text(x + 1.9, 0.5 * (y0 + y1), label, fontsize=7.0, color=C_SLATE,
            ha="left", va="center")


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=(6.3, 6.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 105)
    ax.set_axis_off()

    ax.text(2.0, 102.0, "The material palette on representative stacks",
            fontsize=9.0, color=C_SLATE, weight="bold")

    row1, row2 = 61.0, 10.0
    # (a) high-k metal gate
    draw_stack(ax, 3.0, 13.0, row1, [
        ("Si", "Si sub", 6.5, None),
        ("SiO2", None, 2.2, "IL 1 nm"),
        ("HfO2", None, 2.6, "2 nm"),
        ("TiN", None, 3.2, "5 nm"),
        ("W", None, 6.5, "30 nm"),
    ], "(a)  high-$k$ metal gate")
    ax.text(16.9, row1 + 4.6, "SiO$_2$", fontsize=7.0, color=C_GREY,
            ha="left", va="center")

    # (b) Cu interconnect
    draw_stack(ax, 36.5, 13.0, row1, [
        ("Si", "Si sub", 6.5, None),
        ("SiO2", None, 8.5, "ILD"),
        ("TaN", None, 2.2, "TaN 3 nm"),
        ("Cu", None, 10.0, "100 nm"),
        ("Si3N4", None, 3.0, "cap 20 nm"),
    ], "(b)  Cu interconnect (BEOL)")

    # (c) GAA nanosheet superlattice
    layers_c = [("Si", "Si sub", 6.5, None)]
    for _ in range(4):
        layers_c.append((SIGE30, "", 3.3, None))
        layers_c.append(("Si", "", 2.9, None))
    b = draw_stack(ax, 70.0, 13.0, row1, layers_c,
                   "(c)  GAA nanosheet stack")
    bracket(ax, 84.0, b[1][0], b[-1][1],
            "$\\times$4:\nSi$_{0.7}$Ge$_{0.3}$ 10 nm\nSi 8 nm")

    # (d) GaN-on-SiC HEMT
    draw_stack(ax, 3.0, 13.0, row2, [
        ("SiC-wafer", "4H-SiC sub", 6.5, None),
        ("AlN", None, 2.2, "AlN 100 nm"),
        ("GaN", None, 11.0, "2 $\\mu$m"),
        (ALGAN25, "Al$_{0.25}$Ga$_{0.75}$N", 3.0, "25 nm"),
        ("Si3N4", None, 2.4, "SiN 50 nm"),
    ], "(d)  GaN-on-SiC HEMT")

    # (e) 3D-NAND ON stack
    layers_e = [("Si", "Si sub", 6.5, None)]
    for _ in range(8):
        layers_e.append(("SiO2", "", 1.9, None))
        layers_e.append(("Si3N4", "", 2.1, None))
    b = draw_stack(ax, 36.5, 13.0, row2, layers_e,
                   "(e)  3D-NAND ON stack")
    bracket(ax, 50.5, b[1][0], b[-1][1],
            "$\\times$8:\nSiO$_2$ 25 nm\nSi$_3$N$_4$ 30 nm")

    # (f) W/Si XRR mirror
    layers_f = [("Si", "Si sub", 6.5, None)]
    for _ in range(6):
        layers_f.append(("W", "", 1.8, None))
        layers_f.append(("Si", "", 2.5, None))
    layers_f.append(("SiO2", "", 1.7, None))
    b = draw_stack(ax, 70.0, 13.0, row2, layers_f,
                   "(f)  W/Si XRR mirror")
    bracket(ax, 84.0, b[1][0], b[-2][1], "$\\times$6:\nW 2 nm\nSi 3 nm")
    ax.text(85.9, 0.5 * (b[-1][0] + b[-1][1]) + 1.6, "native SiO$_2$",
            fontsize=7.0, color=C_GREY, ha="left", va="center")

    ax.text(2.0, 2.2,
            "thicknesses indicative, layers drawn for legibility (not to "
            "scale); alloy fills computed with alloy_color()",
            fontsize=7.0, color=C_GREY)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "stack_gallery"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")
    print(f"  Si0.70Ge0.30 = {SIGE30}; Al0.25Ga0.75N = {ALGAN25}")


if __name__ == "__main__":
    main()
