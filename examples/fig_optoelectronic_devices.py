"""fig_optoelectronic_devices.py -- III-V and III-nitride emitters.

Six schematic device generations exercise blanket/repeated deposition,
patterned features, alloy materials, and doped-material shades.  References:

* R. N. Hall et al., Phys. Rev. Lett. 9, 366 (1962),
  https://doi.org/10.1103/PhysRevLett.9.366
* I. Hayashi et al., Appl. Phys. Lett. 17, 109 (1970),
  https://doi.org/10.1063/1.1653326
* H. Kogelnik and C. V. Shank, Appl. Phys. Lett. 18, 152 (1971),
  https://doi.org/10.1063/1.1653605
* H. Soda et al., Jpn. J. Appl. Phys. 18, 2329 (1979),
  https://doi.org/10.1143/JJAP.18.2329
* S. Nakamura et al., Appl. Phys. Lett. 64, 1687 (1994),
  https://doi.org/10.1063/1.111832
* H. X. Jiang et al., Appl. Phys. Lett. 78, 1303 (2001),
  https://doi.org/10.1063/1.1351521

Outputs: ../docs/figures/optoelectronic_devices.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures.process import Rectangle, Wafer
from semi_structures.style import (
    C_GREY, C_SLATE, PLOT_STYLE, doped,
)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"


def gaas_homojunction():
    wafer = Wafer(size=(6.4, 4.2), substrate=doped("GaAs", 0.20),
                  thickness=0.85)
    wafer.add_layer("GaAs", 0.30, label="junction / gain region")
    wafer.add_layer(doped("GaAs", 0.08), 0.55)
    wafer.add_pad("TiN", 1.8, 0.35, 2.8, 3.5, 0.28)
    return wafer


def double_heterostructure():
    wafer = Wafer(size=(6.4, 4.2), substrate="GaAs", thickness=0.65)
    wafer.add_layer("AlGaAs", 0.45)
    wafer.add_layer("GaAs", 0.20, label="active layer")
    wafer.add_layer("AlGaAs", 0.45)
    wafer.add_pad("TiN", 1.55, 0.35, 3.3, 3.5, 0.30)
    return wafer


def dfb_laser():
    wafer = Wafer(size=(6.4, 4.2), substrate="InP", thickness=0.65)
    wafer.add_layer("InGaAsP", 0.22, label="quantum-well active layer")
    wafer.add_layer("InP", 0.45)
    for x in (0.45, 1.35, 2.25, 3.15, 4.05, 4.95, 5.85):
        wafer.add_pad("InGaAsP", x, 0.45, 0.30, 3.3, 0.20)
    return wafer


def vcsel():
    wafer = Wafer(size=(6.4, 4.2), substrate="GaAs", thickness=0.45)
    wafer.add_multilayer([("AlGaAs", 0.16), ("GaAs", 0.14)], repeats=4)
    wafer.add_layer("InGaAs", 0.18, label="quantum wells")
    wafer.add_multilayer([("GaAs", 0.14), ("AlGaAs", 0.16)], repeats=3)
    wafer.add_pad("TiN", 0.45, 0.40, 1.1, 3.4, 0.22)
    wafer.add_pad("TiN", 4.85, 0.40, 1.1, 3.4, 0.22)
    return wafer


def blue_led():
    # GaN-on-sapphire: the transparent substrate is drawn translucent
    wafer = Wafer(size=(6.4, 4.2), substrate="sapphire", thickness=0.55)
    wafer.add_layer(doped("GaN", 0.16), 0.70)
    wafer.add_layer("InGaN", 0.18, label="blue active layer")
    wafer.add_layer("AlGaN", 0.22, label="electron blocking layer")
    wafer.add_layer(doped("GaN", 0.08), 0.42)
    wafer.add_pad("TiN", 0.45, 0.40, 1.1, 3.4, 0.24)
    wafer.add_pad("TiN", 4.85, 0.40, 1.1, 3.4, 0.24)
    return wafer


def micro_led():
    # GaN-on-SiC: a bulk SiC wafer, translucent like sapphire
    wafer = Wafer(size=(6.4, 4.2), substrate="SiC-wafer", thickness=0.55)
    n_gan = wafer.add_layer(doped("GaN", 0.16), 0.70)
    wafer.add_multilayer([("InGaN", 0.12), ("GaN", 0.15)], repeats=4)
    wafer.add_layer(doped("GaN", 0.08), 0.32)
    mesa = Rectangle((3.2, 2.1), (3.9, 2.3))
    wafer.mesa(mesa, stop_on=n_gan, name="micro-LED mesa")
    wafer.add_feature("TiN", Rectangle((3.2, 2.1), (2.1, 1.7)), 0.25)
    return wafer


PANEL_W = 2.0                      # printed width of one panel, in inches


def draw_panel(ax, wafer, title, feature, source, scale=0.82):
    ax.set_xlim(-3.9, 6.5)
    ax.set_ylim(-1.8, 7.9)
    ax.set_aspect("equal")
    ax.set_axis_off()
    # One call: planar flows draw as vector boxes at origin/scale, the mesa
    # flow (a Boolean etch) renders as a solid panel placed at `extent`.
    # The solid render is sized for the printed panel width.
    wafer.render(ax=ax, origin=(0.35, 0.15), scale=scale,
                 extent=(-3.2, 6.2, -0.25, 7.0), print_width_in=PANEL_W,
                 aspect=0.8, zoom=1.0, azimuth=-31, elevation=20)
    ax.text(0.02, 0.98, title, transform=ax.transAxes, fontsize=8.3,
            color=C_SLATE, weight="bold", va="top")
    ax.text(0.02, 0.105, feature, transform=ax.transAxes, fontsize=7.0,
            color=C_SLATE)
    ax.text(0.02, 0.025, source, transform=ax.transAxes, fontsize=7.0,
            color=C_GREY)


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    # Two rows of three rather than three of two: at three columns the figure
    # is landscape and short enough to share a page with its section text,
    # which a 5.4 x 7.3 in portrait block cannot do without being scaled
    # below the 7 pt floor.
    fig, axes = plt.subplots(2, 3, figsize=(6.3, 4.5))
    fig.subplots_adjust(left=0.02, right=0.99, top=0.88, bottom=0.03,
                        hspace=0.16, wspace=0.06)
    fig.suptitle("III-V and III-nitride light emitters",
                 fontsize=11.5, color=C_SLATE, weight="bold", y=0.975)
    fig.text(0.5, 0.917,
             "From homojunctions to heterostructures, resonators, and mesas",
             fontsize=7.8, color=C_GREY, ha="center")

    panels = [
        (gaas_homojunction(), "(a) GaAs junction laser",
         "single-material p-n gain", "Hall et al., PRL 9 (1962)"),
        (double_heterostructure(), "(b) AlGaAs/GaAs DH laser",
         "carrier + optical confinement", "Hayashi et al., APL 17 (1970)"),
        (dfb_laser(), "(c) InP/InGaAsP DFB laser",
         "buried active layer + grating", "Kogelnik & Shank, APL 18 (1971)"),
        (vcsel(), "(d) GaAs/AlGaAs VCSEL",
         "repeated DBRs + vertical cavity", "Soda et al., JJAP 18 (1979)"),
        (blue_led(), "(e) InGaN/GaN blue LED",
         "on sapphire, DH + blocking layer", "Nakamura et al., APL 64 (1994)"),
        (micro_led(), "(f) InGaN/GaN micro-LED",
         "on SiC, etched mesa + MQWs", "Jiang et al., APL 78 (2001)"),
    ]
    for ax, args in zip(axes.flat, panels):
        draw_panel(ax, *args)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "optoelectronic_devices"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
