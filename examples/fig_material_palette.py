"""fig_material_palette.py -- key figure for the material color system.

The palette itself lives in semi_structures.style (MATERIAL, FAMILIES, mix,
validate_materials); this script draws the key and re-validates the laws:
hue = chemical family, lightness = electron density (heavier -> darker,
approximately material density), doped variants retain the host hue, and
alloys interpolate their endpoint colors.

Layout: two panels of equal width on one shared chip grid (five chips per
row everywhere, one chip size everywhere). Coordinates are inches, so one
data unit is one inch and 72 data-milli-units are one point; chip text is
sized from the chip itself and never drops below MIN_PRINT_PT.

Outputs: ../docs/figures/material_palette.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle
from matplotlib.patheffects import withStroke

from semi_structures.style import (
    C_GREY, C_SLATE, FAMILIES, MATERIAL, MATERIAL_ALPHA, MIN_PRINT_PT, PRETTY,
    alpha_for, luminance, mix, style_for, validate_materials,
)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

# ---- geometry (inches) ------------------------------------------------------
# Author at the print width used in the showcase so point sizes are true.
W = 6.3
H = 7.2                       # one family row taller than square
XM = 0.05                     # outer side margin
GUTTER = 0.26                 # gap between the two panels
PANEL_W = (W - 2 * XM - GUTTER) / 2
NCOL = 5                      # chips per row, both panels
PITCH = PANEL_W / NCOL
CHIP_GAP = 0.05
CHIP_W = PITCH - CHIP_GAP
CHIP_H = 0.46
HEX_DROP = 0.035              # chip bottom -> hex-code top
ROW_PITCH = CHIP_H + 0.17     # chip top -> next chip top
TITLE_DROP = 0.21             # family title top -> first chip top
FAMILY_GAP = 0.06             # after the last row of a family
LIGHT_TEXT = "#F4F6F8"
EDGE = "#D0D5DA"

# ---- typography (points): chip text is proportional to the chip ------------
CHIP_H_PT = CHIP_H * 72
NAME_PT = max(MIN_PRINT_PT, round(0.25 * CHIP_H_PT, 1))     # 8.3
RHO_PT = max(MIN_PRINT_PT, round(0.225 * CHIP_H_PT, 1))     # 7.5
HEX_PT = max(MIN_PRINT_PT, round(0.21 * CHIP_H_PT, 1))      # 7.0
FAMILY_PT = 8.8
TITLE_PT = 12.5
LAW_PT = 8.4
NOTE_PT = 7.4
PAD_PT = 2.0                  # horizontal padding inside a chip

_SIZES_USED = []


def _fit(fig, ax, text, size, max_w_pt, **kw):
    """Largest size <= `size` (never < MIN_PRINT_PT) at which `text` fits."""
    renderer = fig.canvas.get_renderer()
    probe = ax.text(0, 0, text, fontsize=size, **kw)
    while True:
        width_pt = probe.get_window_extent(renderer).width * 72 / fig.dpi
        if width_pt <= max_w_pt or size <= MIN_PRINT_PT:
            break
        size = max(MIN_PRINT_PT, round(size - 0.1, 1))
        probe.set_fontsize(size)
    probe.remove()
    _SIZES_USED.append(size)
    return size


def chip(fig, ax, x, y_top, name):
    """One material chip: name (+ rho_e) inside, hex code beneath.

    Translucent materials (``alpha_for(name) < 1``) are drawn at their
    alpha over a slate diagonal stripe so the transparency itself is
    visible; the hex code beneath gains the alpha.
    """
    color, rho = MATERIAL[name]
    alpha = alpha_for(name)
    y = y_top - CHIP_H
    frame = FancyBboxPatch((x, y), CHIP_W, CHIP_H,
                           boxstyle="round,pad=0,rounding_size=0.055",
                           facecolor="none", edgecolor="none")
    ax.add_patch(frame)
    if alpha < 1.0:
        band = 0.14 * CHIP_W
        xa = x + 0.34 * CHIP_W
        stripe = Polygon([(xa, y), (xa + band, y),
                          (xa + band + CHIP_H, y + CHIP_H),
                          (xa + CHIP_H, y + CHIP_H)], closed=True,
                         facecolor=C_SLATE, edgecolor="none", zorder=1.5)
        stripe.set_clip_path(frame)
        ax.add_patch(stripe)
    ax.add_patch(FancyBboxPatch(
        (x, y), CHIP_W, CHIP_H,
        boxstyle="round,pad=0,rounding_size=0.055",
        facecolor=to_rgba(color, alpha),
        edgecolor=C_GREY if name == "vacuum" else EDGE,
        linewidth=0.7, zorder=2))
    text_color = C_SLATE if luminance(color) > 0.30 else LIGHT_TEXT
    # a thin white halo keeps chip text legible where the stripe shows through
    halo = dict(path_effects=[withStroke(linewidth=1.8, foreground="white")]) \
        if alpha < 1.0 else {}
    cx, cy = x + CHIP_W / 2, y + CHIP_H / 2
    max_w = CHIP_W * 72 - 2 * PAD_PT
    label = PRETTY.get(name, name)
    if rho is not None:
        rho_text = f"$\\rho_e$ = {rho:.2f}"
        size = _fit(fig, ax, label, NAME_PT, max_w)
        ax.text(cx, cy + 0.072, label, fontsize=size, color=text_color,
                ha="center", va="center", zorder=3, **halo)
        size = _fit(fig, ax, rho_text, RHO_PT, max_w)
        ax.text(cx, cy - 0.078, rho_text, fontsize=size, color=text_color,
                ha="center", va="center", zorder=3, **halo)
    else:
        size = _fit(fig, ax, label, NAME_PT, max_w)
        ax.text(cx, cy, label, fontsize=size, color=text_color,
                ha="center", va="center", linespacing=1.15, zorder=3, **halo)
    hex_text = color.upper()
    if alpha < 1.0:                       # second line: "α = 0.35"
        hex_text += "\n" + chr(945) + f" = {alpha:.2f}"
    ax.text(cx, y - HEX_DROP, hex_text, fontsize=HEX_PT, color=C_GREY,
            family="monospace", ha="center", va="top", zorder=3,
            linespacing=1.15)
    _SIZES_USED.append(HEX_PT)


def draw_family(fig, ax, x0, y_top, title, names):
    """One family block: title, wrapped rows of chips. Returns the bottom."""
    ax.text(x0, y_top, title, fontsize=FAMILY_PT, color=C_SLATE, va="top")
    y = y_top - TITLE_DROP
    nrows = (len(names) + NCOL - 1) // NCOL
    for i, name in enumerate(names):
        row, col = divmod(i, NCOL)
        chip(fig, ax, x0 + col * PITCH, y - row * ROW_PITCH, name)
    extra = 0.12 if any(alpha_for(n) < 1.0 for n in names) else 0.0
    return y - nrows * ROW_PITCH - FAMILY_GAP - extra


def draw_ramp(ax, x0, y_top, width, a, b, x_mark, marker_label):
    """Endpoint-to-endpoint color ramp with a marked composition."""
    bar_h = 0.20
    bar_top = y_top - 0.13
    ax.text(x0, bar_top + 0.03, a, fontsize=NOTE_PT, color=C_SLATE,
            ha="left", va="bottom")
    ax.text(x0 + width, bar_top + 0.03, b, fontsize=NOTE_PT, color=C_SLATE,
            ha="right", va="bottom")
    xs = np.linspace(0.0, 1.0, 256)
    rgb = np.array([matplotlib.colors.to_rgb(
        mix(MATERIAL[a][0], MATERIAL[b][0], x)) for x in xs])[None, :, :]
    ax.imshow(rgb, extent=(x0, x0 + width, bar_top - bar_h, bar_top),
              aspect="auto", interpolation="bilinear", zorder=2)
    ax.add_patch(Rectangle((x0, bar_top - bar_h), width, bar_h, fill=False,
                           edgecolor=EDGE, lw=0.7, zorder=3))
    xm = x0 + width * x_mark
    ax.plot([xm, xm], [bar_top - bar_h, bar_top], color=C_SLATE, lw=0.7,
            zorder=4)
    ax.plot(xm, bar_top - bar_h - 0.035, marker="^", ms=3.6, color=C_SLATE,
            zorder=4)
    ax.text(xm, bar_top - bar_h - 0.075, marker_label, fontsize=NOTE_PT,
            color=C_SLATE, ha="center", va="top")
    return bar_top - bar_h - 0.075 - 0.13    # bottom of this ramp row


def make_figure():
    plt.rcParams.update(style_for((W, H)))
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_axis_off()

    # ---- header -----------------------------------------------------------
    y = H - 0.10
    ax.text(XM, y, "Material colors for cross-section schematics",
            fontsize=TITLE_PT, color=C_SLATE, weight="bold", va="top")
    y -= 0.27
    laws = [
        "hue = chemical family",
        "lightness = electron density $\\rho_e$ (heavier $\\rightarrow$ "
        "darker)",
        "alloys interpolate their endpoint colors",
        "doped variants retain the host hue and darken only when they must "
        "be distinguished",
    ]
    for i, law in enumerate(laws):
        ax.text(XM + 0.02, y - 0.15 * i, f"{i + 1}", fontsize=LAW_PT,
                color=C_GREY, va="top")
        ax.text(XM + 0.22, y - 0.15 * i, law, fontsize=LAW_PT,
                color=C_SLATE, va="top")
    y_panels = y - 0.15 * len(laws) - 0.16

    fam = dict(FAMILIES)
    left_x = XM
    right_x = XM + PANEL_W + GUTTER

    # ---- left panel: the physical families -------------------------------
    y = y_panels
    y = draw_family(fig, ax, left_x, y,
                    "Group IV – blues (SiC = silicon carbide)",
                    fam[FAMILIES[0][0]])
    y = draw_family(fig, ax, left_x, y, "III–V – greens",
                    fam[FAMILIES[1][0]])
    y = draw_family(fig, ax, left_x, y, "dielectrics – soft sands",
                    fam[FAMILIES[3][0]])
    y = draw_family(fig, ax, left_x, y,
                    "metals – greys and native tints",
                    fam[FAMILIES[5][0]])
    y_left_end = draw_family(fig, ax, left_x, y,
                             "transparent crystals – near-clear, translucent",
                             fam[FAMILIES[7][0]])

    # ---- right panel: nitrides, barriers, packaging, alloys --------------
    y = y_panels
    y = draw_family(fig, ax, right_x, y, "III-nitrides – teals",
                    fam[FAMILIES[2][0]])
    y = draw_family(fig, ax, right_x, y,
                    "barrier nitrides – metallic gold-olive",
                    fam[FAMILIES[4][0]])
    y = draw_family(fig, ax, right_x, y, "neutrals and packaging",
                    fam[FAMILIES[6][0]])

    ax.text(right_x, y, "alloys interpolate endpoint colors",
            fontsize=FAMILY_PT, color=C_SLATE, va="top")
    y -= TITLE_DROP
    ramp_gap = 0.30
    ramp_w = (PANEL_W - ramp_gap) / 2
    ramps = [
        ("Si", "Ge", 0.30, "Si$_{0.7}$Ge$_{0.3}$"),
        ("AlN", "GaN", 0.50, "Al$_{0.5}$Ga$_{0.5}$N"),
        ("GaAs", "InAs", 0.22, "In$_{0.22}$Ga$_{0.78}$As"),
        ("GaN", "InN", 0.15, "In$_{0.15}$Ga$_{0.85}$N"),
    ]
    y_right_end = y
    for j, (a, b, x_mark, lab) in enumerate(ramps):
        col, row = j % 2, j // 2
        row_top = y - row * 0.70
        y_right_end = min(y_right_end, draw_ramp(
            ax, right_x + col * (ramp_w + ramp_gap), row_top, ramp_w,
            a, b, x_mark, lab))

    # ---- footnotes --------------------------------------------------------
    y_notes = min(y_left_end, y_right_end) - 0.16
    ax.text(left_x, y_notes,
            "$\\rho_e$: reference electron density (e Å$^{-3}$) "
            "from bulk density; higher values map to darker fills.\n"
            "Substrate, package and PCB are semantic materials and take "
            "documented colors rather than a $\\rho_e$ shade.\n"
            "Transparent crystals (bulk SiC wafer, sapphire = Al$_2$O$_3$) "
            "are near-clear tints drawn at the stated $\\alpha$ by every "
            "renderer; the stripe shows the transparency.\n"
            "They are distinct from the opaque device color SiC and the "
            "thin-film dielectric Al$_2$O$_3$.",
            fontsize=NOTE_PT, color=C_GREY, va="top", linespacing=1.35)
    ax.text(left_x, y_notes - 0.62,
            "Alloy ramps: $x$ is the right-hand endpoint fraction; RGB "
            "interpolation is a drawing convention, not a physical model.",
            fontsize=NOTE_PT, color=C_GREY, va="top")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "material_palette"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem, (y_left_end, y_right_end, y_notes)


def main():
    validate_materials()
    stem, (yl, yr, yn) = make_figure()
    smallest = min(_SIZES_USED)
    if smallest < MIN_PRINT_PT:
        raise SystemExit(f"text below print floor: {smallest} pt")
    print(f"wrote {stem}.pdf (+ .png); palette laws validated")
    print(f"chip {CHIP_W:.3f} x {CHIP_H:.2f} in; name {NAME_PT} pt, "
          f"rho {RHO_PT} pt, hex {HEX_PT} pt; smallest text {smallest} pt")
    print(f"panel bottoms: left {yl:.2f} in, right {yr:.2f} in; "
          f"notes at {yn:.2f} in")


if __name__ == "__main__":
    main()
