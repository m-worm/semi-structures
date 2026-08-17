"""fig_sic_power_devices.py -- representative 4H-SiC power devices.

All four panels are process-DSL models. Implanted regions replace, rather
than overlap, the drift material; the trench gate uses nested Boolean
etch/fill; and the fin panel uses oxide-isolated wrap gates assembled from
localized DSL features. References are listed in examples/REFERENCES.md.

Outputs: ../docs/figures/sic_power_devices.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Rectangle, Wafer
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE, doped

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

N_PLUS = doped("SiC", 0.28)
N_DRIFT = doped("SiC", 0.08)
P_BODY = doped("SiC", 0.18)
P_PLUS = doped("SiC", 0.34)


def schottky_diode():
    wafer = Wafer(size=(7.2, 4.8), substrate=N_PLUS, thickness=0.65)
    wafer.add_layer(N_DRIFT, 1.75, label="n- drift")
    wafer.add_backside_layer("Al", 0.28)
    wafer.add_pad("TiN", 0.7, 0.55, 5.8, 3.7, 0.32)
    scene = wafer.scene("solid")
    scene.cutaway(y=2.4)
    return scene


def planar_dmos():
    wafer = Wafer(size=(7.2, 4.8), substrate=N_PLUS, thickness=0.60)
    wafer.add_layer(N_DRIFT, 1.70)
    for x in (1.775, 5.425):
        wafer.implant(Rectangle((x, 2.4), (2.65, 4.0)), P_BODY,
                      depth=0.65, name="p-body")
    for x in (1.375, 5.825):
        wafer.implant(Rectangle((x, 2.4), (1.25, 3.4)), N_PLUS,
                      depth=0.35, name="n+ source")
    wafer.add_feature("SiO2", Rectangle((3.6, 2.4), (2.50, 4.10)),
                      0.16)
    wafer.add_feature("TiN", Rectangle((3.6, 2.4), (2.10, 3.70)),
                      0.42, z0=wafer.top + 0.16)
    scene = wafer.model()
    scene.cutaway(y=2.4)
    return scene


def trench_mosfet():
    wafer = Wafer(size=(7.2, 4.8), substrate=N_PLUS, thickness=0.60)
    wafer.add_layer(N_DRIFT, 2.68)
    wafer.implant(Rectangle((3.6, 2.4), (7.2, 4.8)), P_BODY,
                  depth=0.98, name="p-body")
    for x in (1.30, 5.90):
        wafer.implant(Rectangle((x, 2.4), (1.70, 3.8)), N_PLUS,
                      depth=0.36, name="n+ source")
    wafer.implant(Rectangle((3.6, 2.4), (2.30, 4.10)), P_PLUS,
                  z0=1.66, z1=1.88, name="p+ trench shield")

    outer = wafer.etch(Rectangle((3.6, 2.4), (1.90, 3.70)), depth=1.45,
                       name="gate trench")
    wafer.fill(outer, "SiO2")
    inner = wafer.etch(Rectangle((3.6, 2.4), (1.30, 3.10)), depth=1.18,
                       name="gate opening")
    wafer.fill(inner, "TiN")
    scene = wafer.model()
    scene.cutaway(y=2.4)
    return scene


def tri_gate_mosfet():
    wafer = Wafer(size=(7.2, 4.8), substrate=N_PLUS, thickness=0.60)
    wafer.add_layer(N_DRIFT, 1.55)
    fin_base = wafer.top
    fin_height = 1.25
    gate_top = fin_base + fin_height

    for y in (1.0, 2.4, 3.8):
        outer_gate = Rectangle((3.6, y), (2.10, 1.05))
        oxide_opening = Rectangle((3.6, y), (2.10, 0.81))
        fin_opening = Rectangle((3.6, y), (2.10, 0.55))

        wafer.add_feature("TiN", outer_gate, fin_height, z0=fin_base)
        oxide = wafer.etch(oxide_opening, depth=fin_height,
                           surface_z=gate_top, name="gate dielectric opening")
        wafer.fill(oxide, "SiO2")
        fin = wafer.etch(fin_opening, depth=fin_height,
                         surface_z=gate_top, name="fin opening")
        wafer.fill(fin, P_BODY)

        wafer.add_feature(P_BODY, Rectangle((1.775, y), (1.55, 0.55)),
                          fin_height, z0=fin_base)
        wafer.add_feature(P_BODY, Rectangle((5.425, y), (1.55, 0.55)),
                          fin_height, z0=fin_base)
        wafer.add_feature("SiO2", fin_opening, 0.10, z0=gate_top)
        wafer.add_feature("TiN", fin_opening, 0.12, z0=gate_top + 0.10)
        wafer.add_feature(N_PLUS, Rectangle((5.65, y), (1.10, 0.55)),
                          0.28, z0=gate_top)
    # Rectilinear, so vector would be exact; the panel stays a solid render
    # to match its three siblings.
    return wafer.model(backend="solid")


def draw_panel(ax, scene, title, feature, source, *, zoom=0.95,
               azimuth=35, elevation=5):
    image = scene.render_array(window=(900, 720), zoom=zoom,
                               azimuth=azimuth, elevation=elevation)
    ax.imshow(image, extent=(0.0, 1.0, 0.30, 0.92), aspect="auto")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_axis_off()
    ax.text(0.02, 0.985, title, transform=ax.transAxes, fontsize=8.6,
            color=C_SLATE, weight="bold", va="top")
    ax.text(0.02, 0.105, feature, transform=ax.transAxes, fontsize=7.0,
            color=C_SLATE)
    ax.text(0.02, 0.030, source, transform=ax.transAxes, fontsize=7.0,
            color=C_GREY)


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, axes = plt.subplots(2, 2, figsize=(6.5, 6.2))
    fig.subplots_adjust(left=0.035, right=0.985, top=0.91, bottom=0.04,
                        hspace=0.18, wspace=0.07)
    fig.suptitle("4H-SiC power-device structures", fontsize=11.5,
                 color=C_SLATE, weight="bold")
    fig.text(0.5, 0.925,
             "DSL-authored solids; doped shades distinguish SiC regions",
             fontsize=7.6, color=C_GREY, ha="center")

    draw_panel(axes[0, 0], schottky_diode(), "(a) Vertical Schottky diode",
               "front metal / n-drift / n+ substrate / backside metal",
               "Cooper & Agarwal, Proc. IEEE 90 (2002)")
    draw_panel(axes[0, 1], planar_dmos(),
               "(b) Planar double-implanted MOSFET",
               "replacement p-body + n+ source + surface gate",
               "Vathulya & White, IEEE TED 47 (2000)")
    draw_panel(axes[1, 0], trench_mosfet(), "(c) Shielded trench MOSFET",
               "nested oxide/gate fills above a p+ shield implant",
               "Zhou et al., IEEE TED 64 (2017)")
    draw_panel(axes[1, 1], tri_gate_mosfet(), "(d) SiC tri-gate concept",
               "three fins with non-overlapping oxide-isolated wrap gates",
               "Ramamurthy et al., IEEE EDL 42 (2021)", zoom=0.90,
               azimuth=-31, elevation=20)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "sic_power_devices"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
