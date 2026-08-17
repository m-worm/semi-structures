"""fig_gpu_cowos_assembled.py -- the same GPU package, assembled.

The chip-on-wafer-on-substrate (CoWoS-style) package of
``fig_gpu_cowos_exploded.py`` with every level seated: the organic package
substrate and its decoupling capacitors, the silicon interposer on its C4
bump field, and on top the GPU die flanked by six HBM towers. The geometry
is shared with the exploded figure, so the two differ only in the gap
opened between levels and in the viewpoint.

Assembled, the two bump fields disappear: the C4 array sits under the
interposer and the microbump arrays under the dies. That is what the
exploded view is for, and it is why the callouts here name only what a
camera can actually see.

Callouts are stick and ball. Every anchor sits on a face that is visible
from this camera, and the leaders take the text color rather than the
paler default, which reads faintly against grey dies.

Outputs: ../docs/figures/gpu_cowos_assembled.png and .pdf
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures.solid import C_SLATE
from semi_structures.style import PLOT_STYLE
from fig_gpu_cowos_exploded import (
    GPU, HBM_H, INT, INT_XY, SUB, T_BASE, build, die_sites,
)

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

LEADER = C_SLATE          # the palette default reads faintly on grey dies


def make_scene():
    s = build(explode=0.0, labels=False)
    ix, iy = INT_XY
    z_sub = SUB[2]
    z_int = z_sub + 0.7
    z_die = z_int + INT[2] + 0.308

    gx0, gy0, gdx, gdy, _ = die_sites()[0]
    # Both HBM callouts live in the right margin, so both anchor on the right
    # column: a leader to the left column would cross the whole GPU die.
    hbm_front = die_sites()[4]                  # right column, front tower
    hbm_back = die_sites()[6]                   # right column, back tower

    call = dict(size=8.2, marker="dot", line_color=LEADER, line_width=0.8)
    right = dict(justify="right", **call)

    s.label("GPU die",
            anchor=(ix + gx0 + 0.5 * gdx, iy + gy0 + 0.5 * gdy,
                    z_die + GPU[2]),
            via=(0.50, 0.11), position=(0.50, 0.05), justify="center", **call)
    s.label("HBM stacks (x6):\n8 DRAM dies on a base die",
            anchor=(ix + hbm_back[0] + hbm_back[2],
                    iy + hbm_back[1] + 0.5 * hbm_back[3],
                    z_die + T_BASE + 0.5 * (HBM_H - T_BASE)),
            via=(0.78, 0.24), position=(0.97, 0.20), **right)
    s.label("HBM base die",
            anchor=(ix + hbm_front[0] + hbm_front[2],
                    iy + hbm_front[1] + 0.5 * hbm_front[3],
                    z_die + 0.5 * T_BASE),
            via=(0.78, 0.44), position=(0.97, 0.40), **right)
    # Anchored near the front of the interposer's right edge, which projects
    # below the base-die dot, so the two right-hand leaders do not cross.
    s.label("Si interposer",
            anchor=(ix + INT[0], iy + 0.10 * INT[1], z_int + 0.5 * INT[2]),
            via=(0.78, 0.64), position=(0.97, 0.60), **right)
    # One of the three capacitors on the front-left margin: the front-right
    # group would put this leader right across the package.
    s.label("decoupling capacitors",
            anchor=(4.8 + 0.8, 1.6 + 0.45, z_sub + 0.7),
            via=(0.24, 0.72), position=(0.03, 0.68), **call)
    s.label("package substrate",
            anchor=(0.3 * SUB[0], 0.0, 0.5 * SUB[2]),
            via=(0.24, 0.88), position=(0.03, 0.84), **call)
    s.text2d("GPU package, CoWoS-style: assembled", position="lower_right",
             size=10.0)
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(PLOT_STYLE)
    print_width, aspect = 6.3, 0.60
    png = OUT / "gpu_cowos_assembled.png"
    make_scene().render(str(png), print_width_in=print_width, aspect=aspect,
                        zoom=1.05, azimuth=-120.0, elevation=-8.0)

    fig = plt.figure(figsize=(print_width, print_width * aspect))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(plt.imread(png))
    ax.set_axis_off()
    fig.savefig(OUT / "gpu_cowos_assembled.pdf")
    plt.close(fig)
    print(f"wrote {png} and {OUT / 'gpu_cowos_assembled.pdf'}")


if __name__ == "__main__":
    main()
