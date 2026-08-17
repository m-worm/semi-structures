"""Shared materials and publication styling for semi-structures.

Single source of truth for:

* PLOT_STYLE      rcParams shared by all figure scripts
* line palette    LINE_PALETTE order and roles; BLACK is analytic truth only
* semantic colors beams and wavefield channels (saturated, never fills)
* MATERIAL        material-aware fills: hue = chemical family, lightness =
                  electron density within physical families (heavier ->
                  darker); semantic package materials use documented neutral
                  colors; alloys via alloy_color()
* FIGSIZES        the aspect-ratio menu (4:3, 9:5, 1:1, 3:4 and the
                  standard multi-panel combinations) -- pick from the menu,
                  never an arbitrary ratio
* CMAPS           which colormap for which kind of heatmap, and why

Import from here in new figure scripts:

    from semi_structures.style import PLOT_STYLE, LINE_PALETTE, MATERIAL, FIGSIZES
"""
from __future__ import annotations

import numpy as np
from matplotlib.colors import to_rgb

# ----------------------------------------------------------------------------
# rcParams
# ----------------------------------------------------------------------------

PLOT_STYLE = {
    "font.family": "sans-serif",     # figures are sans; the body text is serif
    "mathtext.fontset": "dejavusans",  # math inside figures matches the sans
    "font.size": 9.2,
    "axes.titlesize": 10.2,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.2,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}

# ----------------------------------------------------------------------------
# typography. Figures use sans-serif so annotation reads as annotation against
# the serif body text and survives small sizes. THE size law: author a figure
# at the width it will print (figsize width = printed width, e.g. a
# \textwidth figure is PRINT_TEXTWIDTH_IN wide), so point sizes in the script
# are point sizes on the page. Ladder at print size: panel titles 10, axis
# labels 9.5, ticks 8.5, legends/annotations 8.2, small notes 7.5 -- and
# nothing below MIN_PRINT_PT anywhere. If a dense figure must be authored
# oversize, scale every font with style_for() instead of shrinking in LaTeX.
# ----------------------------------------------------------------------------

PRINT_TEXTWIDTH_IN = 6.3   # printed width of a full-width book figure
MIN_PRINT_PT = 7.0         # hard floor for rendered text at print size


def style_for(figsize, printed_width=None):
    """PLOT_STYLE with fonts scaled for a canvas wider than its print size.

    style_for((12.6, 9), printed_width=6.3) doubles every font so the text
    still lands on the page at ladder size after LaTeX scales the figure.
    """
    factor = figsize[0] / (printed_width or PRINT_TEXTWIDTH_IN)
    style = dict(PLOT_STYLE)
    if factor > 1.0:
        for key in ("font.size", "axes.titlesize", "axes.labelsize",
                    "xtick.labelsize", "ytick.labelsize", "legend.fontsize"):
            style[key] = round(style[key] * factor, 1)
    return style

# ----------------------------------------------------------------------------
# annotation greys and reserved saturated colors (beams, wavefield channels)
# ----------------------------------------------------------------------------

C_SLATE, C_GREY, C_PLATE = "#3d4852", "#8a949c", "#687078"
C_BEAM = "#B0304A"      # incident beam (crimson, schematic convention)
C_SPECULAR = "#255c99"  # specular / reflected channel
C_DIFFRACTED = "#3f7d5b"  # Bragg-diffracted channel
C_EVANESCENT = "#c98a2d"  # evanescent / absorbed

# ----------------------------------------------------------------------------
# line palette: order and roles. BLACK is reserved for analytic ground truth;
# grey carries context curves; guides are dotted grey.
# ----------------------------------------------------------------------------

LINE_PALETTE = [
    ("#255c99", "blue",   "1st series: the result the panel is about"),
    ("#b33a3a", "red",    "2nd series: the contrasting case"),
    ("#3f7d5b", "green",  "3rd series"),
    ("#c98a2d", "amber",  "4th series"),
    ("#7b5ea7", "purple", "5th series (rare: consider panels instead)"),
    ("#8a949c", "grey",   "context and reference curves"),
]
BLACK_TRUTH = ("#000000", "black", "analytic ground truth only")


def series_ramp(n, base="#255c99", lighten=0.72):
    """Single-hue ramp for a SEQUENCE of related curves (e.g. thicknesses).

    Categories take LINE_PALETTE in order; ordered families take one hue at
    graded lightness so the progression is legible without a legend.
    """
    base_rgb = np.array(to_rgb(base))
    out = []
    for k in range(n):
        f = lighten * (1.0 - k / max(n - 1, 1))
        rgb = (1.0 - f) * base_rgb + f * np.ones(3)
        out.append("#" + "".join(f"{int(round(255*v)):02x}" for v in rgb))
    return out

# ----------------------------------------------------------------------------
# material fills
# ----------------------------------------------------------------------------


def mix(hex_a, hex_b, x):
    """Vegard's law for color: linear RGB interpolation at composition x."""
    a, b = np.array(to_rgb(hex_a)), np.array(to_rgb(hex_b))
    rgb = (1.0 - x) * a + x * b
    return "#" + "".join(f"{int(round(255 * v)):02x}" for v in rgb)


# (fill color, electron density in e/A^3 from bulk density). Semantic entries
# such as package and substrate have no single physical density and use None.
# SiC (a IV-IV compound) sits in the group-IV blues with a cyan lean; all
# polytypes (3C/4H/6H) share the one color -- they differ by stacking, not
# composition. Dielectrics are soft low-chroma sands; barrier nitrides are
# metallic gold-olive (TiN's real coating color), deliberately separated
# from the sands in both hue and chroma.
MATERIAL = {
    "Si":    ("#ADD8E6", 0.70),
    "SiC":   ("#92C3CB", 0.96),
    # The darker Ge endpoint keeps the technologically common Si0.7Ge0.3
    # alloy distinct from Si while preserving the Group-IV blue family.
    "Ge":    ("#4F7FA5", 1.41),
    "AlAs":  ("#C4DFC5", 1.11),
    "InP":   ("#AFD5B9", 1.27),
    "GaAs":  ("#93C6A1", 1.42),
    "InAs":  ("#78AD8C", 1.56),
    "AlN":   ("#C2E4DE", 0.96),
    "GaN":   ("#82BFB7", 1.68),
    "InN":   ("#65A9A2", 1.90),
    "SiO2":  ("#F2EAD8", 0.66),
    "Si3N4": ("#E5CFA3", 0.95),
    "Al2O3": ("#DEC6A6", 1.18),
    "HfO2":  ("#C6A886", 2.88),
    "TiN":   ("#E5C766", 1.47),
    "TaN":   ("#9C8F62", 3.39),
    "Al":    ("#DADDE0", 0.78),
    # Tin is the default solder-ball material. Its neutral grey follows the
    # metal lightness sequence at rho_e ~= 1.85 e/A^3.
    "Sn":    ("#B7BBC0", 1.85),
    "Cu":    ("#D5A292", 2.46),
    "W":     ("#8A929C", 4.67),
    "vacuum":    ("#FFFFFF", 0.00),
    "substrate": ("#DCE0E4", None),
    # Semantic packaging materials: composites with no single physical
    # density, so they take documented colors rather than a rho_e shade.
    # Package (mould compound / laminate) is a dark grey, clearly darker than
    # W but never the reserved black; PCB is the solder-mask green of a
    # printed circuit board (used in packaging figures, not beside III-Vs).
    "package":   ("#50565D", None),
    "PCB":       ("#2F7D4F", None),
    "resist":    ("#EBD3E0", 0.40),
}
MATERIAL["SiGe"] = (mix(MATERIAL["Si"][0], MATERIAL["Ge"][0], 0.5), 1.06)
MATERIAL["AlGaN"] = (mix(MATERIAL["AlN"][0], MATERIAL["GaN"][0], 0.5), 1.32)
MATERIAL["AlGaAs"] = (mix(MATERIAL["AlAs"][0], MATERIAL["GaAs"][0], 0.65),
                       1.31)
MATERIAL["InGaAs"] = (mix(MATERIAL["GaAs"][0], MATERIAL["InAs"][0], 0.22),
                       1.45)
MATERIAL["InGaAsP"] = (mix(MATERIAL["InP"][0], MATERIAL["InGaAs"][0], 0.52),
                        1.36)
MATERIAL["InGaN"] = (mix(MATERIAL["GaN"][0], MATERIAL["InN"][0], 0.15),
                      1.71)


def alloy_color(end_a, end_b, x):
    """Fill for the random alloy A(1-x)B(x) between two MATERIAL endpoints."""
    return mix(MATERIAL[end_a][0], MATERIAL[end_b][0], x)


def doped(host, step=0.10):
    """Dilute doped layers (Si:P, SiGe:B, Si:As) keep the host color; use
    this one-shade-darker variant only when the layer must be told apart
    from the host in the same figure. X-ray-wise they are the host."""
    return mix(MATERIAL[host][0], "#2f3a42", step)


MATERIAL["SiP"] = (doped("Si"), 0.71)   # heavily P-doped epi Si (Si:P)

# Transparent single-crystal substrates. Sapphire (bulk Al2O3) is
# colorless and bulk SiC wafers are translucent (pale amber-olive), and
# figures of GaN-on-sapphire LEDs, GaN-on-SiC HEMTs or X-ray substrates
# read better when the wafer is drawn that way. They are separate entries
# from the opaque device colors "SiC" (silicon carbide device regions of any
# polytype, the base of the doped() ladder in the SiC power figure) and
# "Al2O3" (thin-film dielectric): near-clear tints of the crystal's real
# appearance, and every renderer draws them with the alpha in
# MATERIAL_ALPHA (matplotlib alpha; PyVista opacity). Lightness still
# tracks rho_e inside the family.
MATERIAL["SiC-wafer"] = ("#ECEDD8", 0.96)
MATERIAL["sapphire"] = ("#DDE5F2", 1.18)
MATERIAL_ALPHA = {"SiC-wafer": 0.45, "sapphire": 0.35}


def alpha_for(material):
    """Default drawing alpha of a material name (1.0 for everything but the
    transparent crystals; raw hex colors are opaque)."""
    return MATERIAL_ALPHA.get(material, 1.0)


FAMILIES = [
    ("Group IV $-$ blues (SiC = silicon carbide, cyan-leaned; polytypes "
     "share one color)",
     ["Si", "SiP", "SiC", "SiGe", "Ge"]),
    ("III$-$V $-$ greens", ["AlAs", "InP", "AlGaAs", "InGaAsP",
                            "GaAs", "InGaAs", "InAs"]),
    ("III$-$nitrides $-$ teals", ["AlN", "AlGaN", "GaN", "InGaN",
                                   "InN"]),
    ("dielectrics $-$ soft sands", ["SiO2", "Si3N4", "Al2O3", "HfO2"]),
    ("barrier nitrides $-$ metallic gold-olive (their real coating colors)",
     ["TiN", "TaN"]),
    ("metals $-$ greys, except native tints", ["Al", "Sn", "Cu", "W"]),
    ("neutrals and packaging", ["vacuum", "substrate", "package", "PCB",
                                "resist"]),
    ("transparent crystals $-$ near-clear tints, drawn translucent",
     ["SiC-wafer", "sapphire"]),
]
PRETTY = {"SiO2": "SiO$_2$", "Si3N4": "Si$_3$N$_4$", "Al2O3": "Al$_2$O$_3$",
          "HfO2": "HfO$_2$", "SiP": "Si:P", "vacuum": "vacuum",
          "AlGaAs": "AlGaAs", "InGaAs": "InGaAs",
          "InGaAsP": "InGaAsP", "InGaN": "InGaN",
          "substrate": "generic\nsubstrate", "package": "package",
          "PCB": "PCB", "resist": "photoresist",
          "SiC-wafer": "SiC wafer", "sapphire": "sapphire"}


def luminance(hex_color):
    """Relative luminance with sRGB linearization."""
    rgb = np.array(to_rgb(hex_color))
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])


def validate_materials():
    """Assert the palette laws: lightness tracks rho_e inside every family,
    and each fill has contrast with its automatically selected label color."""
    for family, names in FAMILIES:
        items = sorted((MATERIAL[n][1], luminance(MATERIAL[n][0]), n)
                       for n in names if MATERIAL[n][1] is not None)
        lums = [lum for _, lum, _ in items]
        if any(b >= a for a, b in zip(lums, lums[1:])):
            raise RuntimeError(f"lightness does not track rho_e in: {family}")
    for name, (color, _) in MATERIAL.items():
        fill_lum = luminance(color)
        label = C_SLATE if fill_lum > 0.30 else "#F4F6F8"
        label_lum = luminance(label)
        contrast = (max(fill_lum, label_lum) + 0.05) / (
            min(fill_lum, label_lum) + 0.05)
        if contrast < 2.0:
            raise RuntimeError(f"label contrast is too low for: {name}")

# ----------------------------------------------------------------------------
# aspect-ratio menu (inches). Pick from the menu; panels in one figure share
# one ratio (designated 1/3-height strips excepted).
# ----------------------------------------------------------------------------

FIGSIZES = {
    "single_43":   (7.2, 5.4),    # default single x-y chart
    "wide_95":     (9.9, 5.5),    # long scans: angle/energy series, spectra
    "square":      (6.2, 6.2),    # maps, parity plots, phasors
    "tall_34":     (5.0, 6.67),   # depth profiles (z downward)
    "two_43":      (10.8, 4.05),  # two 4:3 panels side by side
    "wide_strip":  (9.9, 7.3),    # 9:5 panel over a 1/3-height strip
    "three_11":    (11.2, 3.73),  # three square panels in a row
    "map_profile": (8.8, 6.2),    # square map + narrow side profile
}

# ----------------------------------------------------------------------------
# heatmap colormaps: which, for what, and why
# ----------------------------------------------------------------------------

CMAPS = [
    ("viridis",  "positive scalar fields: intensity, $|E|^2$, visibility",
     "perceptually uniform, colorblind-safe, survives grayscale"),
    ("inferno",  "log-scaled detector counts",
     "black floor reads as zero counts"),
    ("RdBu_r",   "signed fields: residuals, strain, $\\Delta$ from reference",
     "diverging; ALWAYS symmetric limits so white means zero"),
    ("twilight", "phase, azimuth, orientation",
     "cyclic: the two ends meet"),
    ("gray",     "radiographs and topographs",
     "domain convention; reads as image, not field"),
]
CMAP_RULES = ("label every colorbar with units; log scales get decade "
              "ticks; never jet/rainbow (luminance reversals invent edges)")
CMAP_REFERENCE = ("matplotlib.org/stable/users/explain/colors/"
                  "colormaps.html")


if __name__ == "__main__":
    validate_materials()
    print("material palette laws validated")
    for fam, names in FAMILIES:
        for n in names:
            c, r = MATERIAL[n]
            print(f"  {n:10s} {c.upper()}  rho_e="
                  f"{'-' if r is None else f'{r:.2f}'}")
    print("line order: " + ", ".join(f"{n} {c.upper()}"
                                     for c, n, _ in LINE_PALETTE))
