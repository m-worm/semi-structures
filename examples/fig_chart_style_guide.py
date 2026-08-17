"""fig_chart_style_guide.py -- key figure for the chart rules.

Draws the monograph chart system defined in semi_structures.style:

* line palette: colors, ORDER, and roles; black is analytic truth only;
  categories take the palette in order, ordered families take a one-hue
  ramp (series_ramp).
* aspect ratios: a menu (4:3, 9:5, 1:1, 3:4), not a free choice, and the
  standard multi-panel combinations built from it.
* heatmap colormaps: which for what, and why; diverging maps always get
  symmetric limits.
* typography: sans-serif figure text, author at print width, the size
  ladder with a 7 pt floor.

Outputs: ../docs/figures/chart_style_guide.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from semi_structures.style import (
    BLACK_TRUTH, C_GREY, C_SLATE, CMAP_REFERENCE, CMAP_RULES, CMAPS,
    LINE_PALETTE, series_ramp, style_for,
)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"
FIGSIZE = (11.8, 9.0)


def make_figure():
    plt.rcParams.update(style_for(FIGSIZE))
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_axis_off()

    ax.text(1.5, 97.6, "Chart rules: lines, aspect ratios, heatmaps, type",
            fontsize=13.0, color=C_SLATE, weight="bold")

    # ---- line palette and order -------------------------------------------
    ax.text(1.5, 92.6, "line colors, in order", fontsize=9.0, color=C_SLATE)
    rows = list(LINE_PALETTE) + [BLACK_TRUTH]
    for i, (color, name, role) in enumerate(rows):
        y = 89.2 - 3.15 * i
        ax.add_patch(plt.Rectangle((1.5, y), 4.6, 2.2, facecolor=color,
                                   edgecolor="none"))
        ax.text(7.0, y + 1.1, f"{name}:", fontsize=7.6, color=C_SLATE,
                va="center", weight="bold")
        ax.text(13.6, y + 1.1, f"{color.upper()}   {role}", fontsize=7.3,
                color=C_SLATE, va="center")
    ax.text(1.5, 66.0,
            "solid = model or result    dashed = derived / reference\n"
            "dotted = guides and thresholds    markers = measured data",
            fontsize=7.4, color=C_GREY, va="top", linespacing=1.5)

    # mini demos: categories in palette order; ordered series as a ramp
    demo1 = fig.add_axes([0.043, 0.415, 0.165, 0.145])
    x = np.linspace(0.0, 1.0, 240)
    for k, (color, _, _) in enumerate(LINE_PALETTE[:4]):
        demo1.plot(x, np.exp(-2.1 * x) * np.cos(2 * np.pi * (2.1 * x))
                   + 0.55 * (3 - k), color=color, lw=1.3)
    demo1.set_xticks([])
    demo1.set_yticks([])
    demo1.set_title("categories: palette order", fontsize=7.4,
                    color=C_SLATE)
    demo2 = fig.add_axes([0.245, 0.415, 0.165, 0.145])
    for k, color in enumerate(series_ramp(5)):
        demo2.semilogy(x, np.exp(-x / (0.10 + 0.16 * k)) + 1e-3,
                       color=color, lw=1.3)
    demo2.set_xticks([])
    demo2.set_yticks([])
    demo2.set_title("ordered series: one-hue ramp", fontsize=7.4,
                    color=C_SLATE)

    # ---- typography --------------------------------------------------------
    ax.text(1.5, 33.6, "type in figures", fontsize=9.0, color=C_SLATE)
    for i, rule in enumerate([
            "sans-serif in figures; the body text is serif $-$ annotation "
            "reads as annotation",
            "author at print width: figsize width = printed width, so pt "
            "in the script = pt on the page",
            "oversize canvases: scale fonts with style_for(); never "
            "shrink a finished figure in LaTeX"]):
        ax.text(1.5, 30.6 - 2.5 * i, rule, fontsize=7.6, color=C_SLATE)
    ladder = [(10.0, "panel title"), (9.5, "axis labels"),
              (8.5, "tick labels"), (8.2, "legend, annotations"),
              (7.0, "floor $-$ nothing smaller")]
    y = 20.6
    for size, label in ladder:
        ax.text(2.5, y, f"{size:g} pt", fontsize=size, color=C_SLATE)
        ax.text(13.6, y, label, fontsize=7.4, color=C_GREY)
        y -= 1.15 * size / 2.83 + 1.7
    # ---- aspect-ratio menu -------------------------------------------------
    ax.text(52.0, 92.6, "aspect ratios: a menu, not a choice",
            fontsize=9.0, color=C_SLATE)
    menu = [("4:3", 10.7, "default single\n$x$$-$$y$ chart"),
            ("9:5", 14.4, "long scans,\nspectra, kinetics"),
            ("1:1", 8.0, "maps, parity,\nphasors"),
            ("3:4", 6.0, "depth profiles\n($z$ downward)")]
    x0 = 52.0
    for name, w, use in menu:
        ax.add_patch(plt.Rectangle((x0, 81.6), w, 8.0, fill=False,
                                   edgecolor=C_SLATE, lw=1.1))
        ax.text(x0 + w / 2, 85.6, name, fontsize=8.6, color=C_SLATE,
                ha="center", va="center")
        ax.text(x0 + w / 2, 80.4, use, fontsize=7.0, color=C_GREY,
                ha="center", va="top", linespacing=1.4)
        x0 += w + 2.4

    ax.text(52.0, 73.4, "multi-panel: combine menu items "
            "(one ratio per figure; strips excepted)",
            fontsize=8.2, color=C_SLATE)
    def frame(x, y, w, h):
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=False,
                                   edgecolor=C_GREY, lw=0.9))
    # two 4:3
    frame(52.0, 64.6, 6.0, 4.5)
    frame(58.6, 64.6, 6.0, 4.5)
    ax.text(58.3, 62.0, "two 4:3\ncompare cases", fontsize=7.0,
            color=C_GREY, ha="center", va="top", linespacing=1.35)
    # 9:5 over a 1/3 strip
    frame(68.4, 66.1, 8.1, 4.5)
    frame(68.4, 64.4, 8.1, 1.35)
    ax.text(72.4, 62.0, "9:5 + strip\nfit + residuals", fontsize=7.0,
            color=C_GREY, ha="center", va="top", linespacing=1.35)
    # three 1:1
    for k in range(3):
        frame(80.0 + 4.6 * k, 64.8, 4.2, 4.2)
    ax.text(86.6, 62.0, "three 1:1\nmap series", fontsize=7.0,
            color=C_GREY, ha="center", va="top", linespacing=1.35)
    # map + side profile
    frame(94.2, 64.8, 4.2, 4.2)
    frame(98.7, 64.8, 1.3, 4.2)
    ax.text(97.1, 62.0, "1:1 + strip\nmap + cut", fontsize=7.0,
            color=C_GREY, ha="center", va="top", linespacing=1.35)

    # ---- heatmaps ----------------------------------------------------------
    ax.text(52.0, 55.2, "heatmaps: one map per meaning", fontsize=9.0,
            color=C_SLATE)
    grad = np.linspace(0, 1, 160)[None, :]
    y0 = 50.2
    for cmap, use, why in CMAPS:
        ax.imshow(grad, extent=(52.0, 68.0, y0, y0 + 2.1), cmap=cmap,
                  aspect="auto", zorder=2)
        ax.add_patch(plt.Rectangle((52.0, y0), 16.0, 2.1, fill=False,
                                   edgecolor="#c8cdd2", lw=0.6, zorder=3))
        ax.text(69.0, y0 + 1.55, f"{cmap}:  {use}", fontsize=7.2,
                color=C_SLATE, va="center")
        ax.text(69.0, y0 - 0.15, why, fontsize=7.0, color=C_GREY,
                va="center")
        y0 -= 4.55
    rules_1, rules_2 = CMAP_RULES.split("; never")
    ax.text(52.0, y0 + 1.2, rules_1, fontsize=7.0, color=C_SLATE,
            style="italic")
    ax.text(52.0, y0 - 0.7, "never" + rules_2, fontsize=7.0, color=C_SLATE,
            style="italic")
    ax.text(52.0, y0 - 2.8, "reference: " + CMAP_REFERENCE, fontsize=7.0,
            color=C_GREY)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "chart_style_guide"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
