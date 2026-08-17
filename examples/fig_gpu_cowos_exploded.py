"""fig_gpu_cowos_exploded.py -- a modern GPU package, exploded CoWoS view.

A chip-on-wafer-on-substrate (CoWoS-style) GPU package: an organic package
substrate, the C4 bump field, a silicon interposer, the microbump fields,
and on top a large GPU die flanked by six HBM towers (three per side, as
on a current data-centre GPU). Panel (a) is the exploded assembly with
corner guide lines tying every level to the one below; panel (b) is the
same package assembled, seen from the same camera.

The composition follows two supplied references -- a top-down photograph
of an H100 package with the package substrate, interposer, GPU die and HBM
sites marked out, and a foundry illustration of an exploded CoWoS stack
(substrate, interposer, SoC, HBM). Geometry, dimensions and colors are new;
provenance is recorded in ``examples/REFERENCES.md`` and neither image is
redistributed.

Material language (packaging view, as in fig_hbm_labeled.py): PCB green
substrate, Sn C4 bumps, Cu microbumps and HBM bond layers, silicon parts
in the neutral die grey with the logic dies (GPU, HBM base dies) one shade
darker. Color means material; the callouts carry the roles.

Outputs: ../docs/figures/gpu_cowos_exploded.png and gpu_cowos_exploded.pdf
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures.solid import Scene
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE, doped

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

DIE = "substrate"                 # interposer, DRAM dies: neutral die grey
LOGIC = doped("substrate", 0.14)  # GPU and HBM base dies: one shade darker

# ---- layout (model units, roughly mm) ---------------------------------------
SUB = (60.0, 52.0, 2.0)                       # package substrate
INT = (48.0, 38.0, 0.7)                       # Si interposer
INT_XY = ((SUB[0] - INT[0]) / 2, (SUB[1] - INT[1]) / 2)
GPU = (24.0, 30.0, 1.0)                       # GPU die (portrait, as H100)
HBM = (10.0, 11.0)                            # HBM tower footprint
HBM_GAP = 1.0                                 # HBM to GPU / HBM to HBM
N_DRAM, T_DRAM, T_BOND, T_BASE = 8, 0.22, 0.05, 0.5
HBM_H = T_BASE + N_DRAM * (T_BOND + T_DRAM)   # 2.66: a little above the GPU

C4_PITCH, C4_R = 2.4, 0.5                     # Sn bumps, substrate/interposer
UB_PITCH, UB_R = 1.5, 0.22                    # Cu microbumps, interposer/dies


def die_sites():
    """(x0, y0, dx, dy, kind) for the GPU and the six HBM towers, in
    interposer-relative coordinates centred on the interposer."""
    cx, cy = INT[0] / 2, INT[1] / 2
    gx0, gy0 = cx - GPU[0] / 2, cy - GPU[1] / 2
    sites = [(gx0, gy0, GPU[0], GPU[1], "gpu")]
    col_h = 3 * HBM[1] + 2 * HBM_GAP
    y_start = cy - col_h / 2
    for x0 in (gx0 - HBM_GAP - HBM[0], gx0 + GPU[0] + HBM_GAP):
        for k in range(3):
            sites.append((x0, y_start + k * (HBM[1] + HBM_GAP),
                          HBM[0], HBM[1], "hbm"))
    return sites


def build(explode=7.0, labels=True):
    """``explode`` is the vertical gap opened between levels (0 = assembled)."""
    s = Scene()
    ix, iy = INT_XY

    # Level 0: package substrate and its C4 bump field (drawn on the
    # substrate so the array reads as a field under the interposer), plus
    # the rows of decoupling capacitors along the substrate margins.
    s.box((0, 0, 0), SUB, "PCB")
    z_sub = SUB[2]
    s.sphere_array((ix + 1.6, ix + INT[0] - 1.6), (iy + 1.6, iy + INT[1] - 1.6),
                   C4_PITCH, z=z_sub + 0.55 * C4_R, r=C4_R, material="Sn")
    cap = (1.6, 0.9, 0.7)
    for i in range(24):                                   # back row
        s.box((3.0 + i * 2.3, SUB[1] - 3.2, z_sub), cap, "package")
    for x0 in (2.5, 4.8, 7.1, SUB[0] - 4.1, SUB[0] - 6.4, SUB[0] - 8.7):
        s.box((x0, 1.6, z_sub), cap, "package")           # front corners

    # Level 1: Si interposer, floating ``explode`` above the bump tops.
    z_int = z_sub + 1.4 * C4_R + explode
    s.box((ix, iy, z_int), INT, DIE)
    z_int_top = z_int + INT[2]

    # Cu microbump fields on the interposer under every die footprint.
    for x0, y0, dx, dy, _ in die_sites():
        s.sphere_array((ix + x0 + 0.8, ix + x0 + dx - 0.8),
                       (iy + y0 + 0.8, iy + y0 + dy - 0.8), UB_PITCH,
                       z=z_int_top + 0.55 * UB_R, r=UB_R, material="Cu")

    # Level 2: GPU die and six HBM towers.
    z_die = z_int_top + 1.4 * UB_R + explode
    for x0, y0, dx, dy, kind in die_sites():
        X, Y = ix + x0, iy + y0
        if kind == "gpu":
            s.box((X, Y, z_die), (dx, dy, GPU[2]), LOGIC)
        else:
            s.box((X, Y, z_die), (dx, dy, T_BASE), LOGIC)      # base die
            z = z_die + T_BASE
            for _ in range(N_DRAM):
                s.box((X + 0.3, Y + 0.3, z), (dx - 0.6, dy - 0.6, T_BOND),
                      "Cu")
                s.box((X, Y, z + T_BOND), (dx, dy, T_DRAM), DIE)
                z += T_BOND + T_DRAM

    # Exploded-view guide lines: thin 3D leaders (empty labels) from the
    # interposer corners to the substrate and from the GPU corners to the
    # interposer; geometry occludes them like any 3D line.
    if explode > 0:
        for cx_, cy_ in ((ix, iy), (ix + INT[0], iy), (ix, iy + INT[1]),
                         (ix + INT[0], iy + INT[1])):
            s.label("", anchor=(cx_, cy_, z_int),
                    position=(cx_, cy_, z_sub), line_width=0.5)
        gx0, gy0, gdx, gdy, _ = die_sites()[0]
        for cx_, cy_ in ((ix + gx0, iy + gy0), (ix + gx0 + gdx, iy + gy0),
                         (ix + gx0, iy + gy0 + gdy),
                         (ix + gx0 + gdx, iy + gy0 + gdy)):
            s.label("", anchor=(cx_, cy_, z_die),
                    position=(cx_, cy_, z_int_top), line_width=0.5)

    if not labels:
        return s

    # ---- callouts: points at the print width declared in main() ----------
    # Screen positions assume the camera in main(): from -y with a little
    # +x, ~27 deg above the horizon, so x runs left to right across the
    # image and +y recedes. HBM columns sit left and right of the GPU;
    # labels live in the white margins either side, the GPU label above.
    gx0, gy0, gdx, gdy, _ = die_sites()[0]
    hbm_l = die_sites()[1]                       # left column, front tower
    hbm_r = die_sites()[6]                       # right column, back tower
    s.label("GPU die", anchor=(ix + gx0 + 0.5 * gdx, iy + gy0 + 0.75 * gdy,
                               z_die + GPU[2]),
            position=(0.50, 0.06), justify="center", size=8.2)
    s.label("HBM stacks (x6):\n8 DRAM dies on a base die",
            anchor=(ix + hbm_r[0] + 0.5 * hbm_r[2],
                    iy + hbm_r[1] + 0.5 * hbm_r[3], z_die + HBM_H),
            via=(0.72, 0.22), position=(0.97, 0.22), justify="right", size=8.2)
    s.label("Cu microbumps", anchor=(ix + INT[0] - 3.5, iy + 3.0,
                                     z_int_top + 1.6 * UB_R),
            via=(0.84, 0.50), position=(0.97, 0.50), justify="right", size=8.2)
    s.label("Si interposer", anchor=(ix + INT[0], iy + 0.35 * INT[1],
                                     z_int + INT[2] / 2),
            via=(0.86, 0.62), position=(0.97, 0.62), justify="right", size=8.2)
    s.label("decoupling capacitors", anchor=(SUB[0] - 3.3, 2.05, z_sub + 0.7),
            via=(0.86, 0.80), position=(0.97, 0.80), justify="right", size=8.2)
    s.label("HBM base die", anchor=(ix + hbm_l[0] + 0.5 * hbm_l[2],
                                    iy + hbm_l[1], z_die + T_BASE / 2),
            via=(0.16, 0.42), position=(0.03, 0.42), size=8.2)
    s.label("Sn C4 bumps", anchor=(ix + 3.0, iy + 3.0, z_sub + 1.6 * C4_R),
            via=(0.16, 0.66), position=(0.03, 0.66), size=8.2)
    s.label("package substrate", anchor=(0.22 * SUB[0], 0.0, SUB[2] / 2),
            via=(0.16, 0.90), position=(0.03, 0.90), size=8.2)
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print_width, aspect = 6.3, 0.72
    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(print_width, print_width * aspect))

    # Main panel: the exploded stack, camera from -y (a little +x), about
    # 27 deg above the horizon -- the viewpoint of the CoWoS reference.
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    exploded = build(explode=16.0)
    exploded.text2d("GPU package, CoWoS-style: exploded view",
                    position="lower_right", size=10.0)
    ax.imshow(exploded.render_array(print_width_in=print_width, aspect=aspect,
                                    zoom=1.15, azimuth=-120.0, elevation=-8.0))
    ax.set_axis_off()

    # Inset, upper left: the same package assembled, seen almost from
    # above -- the plan view of the package photograph (three HBM sites
    # either side of the GPU on the interposer, capacitors on the margins).
    w_in = 0.24
    ax_b = fig.add_axes([0.02, 1.0 - 0.02 - w_in * 0.78 / aspect, w_in,
                         w_in * 0.78 / aspect])
    assembled = build(explode=0.0, labels=False)
    ax_b.imshow(assembled.render_array(print_width_in=w_in * print_width,
                                       aspect=0.78, zoom=1.9, azimuth=-135.0,
                                       elevation=50.0))
    ax_b.set_axis_off()
    ax_b.text(0.5, -0.03, "assembled, plan view", transform=ax_b.transAxes,
              fontsize=7.5, color=C_SLATE, ha="center", va="top")

    fig.savefig(OUT / "gpu_cowos_exploded.png", dpi=300)
    fig.savefig(OUT / "gpu_cowos_exploded.pdf")
    plt.close(fig)
    print(f"wrote {OUT / 'gpu_cowos_exploded.png'} and "
          f"{OUT / 'gpu_cowos_exploded.pdf'}")


if __name__ == "__main__":
    main()
