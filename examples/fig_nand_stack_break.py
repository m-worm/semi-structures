"""fig_nand_stack_break.py -- a 100-pair 3D-NAND ON stack drawn with a break.

One hundred SiO2/Si3N4 pairs on a Si substrate would be unreadable at
figure scale, so ``add_multilayer(..., repeats=100, show=(10, 5))`` deposits
only the bottom ten and top five repeats with an empty break between them;
the ``StackBreak`` records that 85 are hidden and ``Wafer.render()`` marks
the block with a bracket. Everything crossing the break -- films, the slit,
the memory holes and their fills -- is cut there by both renderers.

(a) vector backend: a rectangular slit etched through the drawn stack
    (exact rectilinear geometry, vector PDF);
(b) solid backend: a hexagonal memory-hole array with poly-Si channels.

Outputs: ../docs/figures/nand_stack_break.pdf (+ .png)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Circle, Rectangle, Wafer, hex_lattice, nm, um
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

PAIR = [("SiO2", 25 * nm), ("Si3N4", 30 * nm)]
SIZE = (1.6 * um, 1.1 * um)


def stack(name="ON"):
    """Si substrate, a 100-pair ON stack drawn as bottom 10 + top 5."""
    wafer = Wafer(size=SIZE, substrate="Si", thickness=140 * nm, name="Si")
    wafer.add_layer("SiO2", 40 * nm, name="buffer oxide")
    wafer.add_multilayer(PAIR, repeats=100, show=(10, 5), gap=110 * nm,
                         name=name, unit="pairs")
    return wafer


def slit_stack():
    wafer = stack()
    depth = wafer.top - wafer.substrate_top
    slit = wafer.etch(Rectangle((SIZE[0] / 2, SIZE[1] / 2),
                                (90 * nm, SIZE[1])), depth=depth, name="slit")
    wafer.fill(slit, "SiO2", name="slit fill")
    return wafer


def hole_stack():
    wafer = stack()
    depth = wafer.top - wafer.substrate_top
    for c in hex_lattice((0.1 * um, SIZE[0] - 0.1 * um),
                         (0.1 * um, SIZE[1] - 0.1 * um), 0.34 * um,
                         margin=0.12 * um, axis="y"):
        hole = wafer.etch(Circle(c, radius=95 * nm), depth=depth,
                          name="memory hole")
        wafer.fill(hole, "Si", name="poly-Si channel")
    return wafer


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(6.3, 5.0))
    grid = fig.add_gridspec(2, 2, height_ratios=(0.9, 0.8), left=0.01,
                            right=0.99, top=0.93, bottom=0.03, wspace=0.05,
                            hspace=0.02)
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    ax_c = fig.add_subplot(grid[1, :])

    ax = axes[0]
    ax.set_aspect("equal")
    ax.set_axis_off()
    slit_stack().render(ax=ax, origin=(0.0, 0.0), scale=1.0)
    ax.set_title("(a) vector: 100-pair ON stack, oxide-filled slit",
                 fontsize=8.3, color=C_SLATE, weight="bold", loc="left",
                 pad=4)
    ax.autoscale_view()
    x0, x1 = ax.get_xlim()
    ax.set_xlim(x0, x1 + 0.34 * (x1 - x0))       # room for the bracket text

    ax = axes[1]
    hole_stack().render(ax=ax, print_width_in=3.1, aspect=0.72, zoom=0.86,
                        azimuth=-32, elevation=18)
    ax.set_title("(b) solid: hexagonal memory holes, poly-Si channels",
                 fontsize=8.3, color=C_SLATE, weight="bold", loc="left",
                 pad=4)

    # (c) the side-on view: the same hole stack cut through a row of holes
    hole_stack().render(ax=ax_c, view="section", y=SIZE[1] / 2 + 0.05 * um,
                        labels=["Si", "buffer oxide", "poly-Si channel"])
    ax_c.set_title("(c) 2D cross-section through a row of memory holes: "
                   "break marks and bracket", fontsize=8.3, color=C_SLATE,
                   weight="bold", loc="left", pad=4)

    fig.text(0.5, 0.965,
             "add_multilayer(ON pair, repeats=100, show=(10, 5)): "
             "bottom 10 and top 5 pairs drawn, 85 elided at the break",
             fontsize=7.4, color=C_GREY, ha="center")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "nand_stack_break"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
