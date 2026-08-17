"""fig_dsl_feature_tour.py -- boolean-solid process DSL feature tour.

Six snapshots show the same structure accumulating process steps. This is
the compact regression and example figure for the readable ``Wafer``
language: substrate construction, blanket and repeated deposition,
depth-controlled rectangle, circle and ellipse etches, exact-shape fill with
optional overfill, and a patterned top layer.

The three etched openings sit on one line at a constant pitch, and the top
layer is a 1D grating of equal lines, so the figure reads as a deliberate
layout rather than as scattered test shapes. All panels use the
trimesh/manifold3d solid model and the PyVista renderer. ``backend="auto"``
selects that path once an etch or fill appears.

Outputs: ../docs/figures/dsl_feature_tour.pdf (+ .png)
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures.process import Circle, Ellipse, Rectangle, Wafer
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

DIAMETER = 9.0                      # wafer diameter, model units
CENTER = DIAMETER / 2
FEATURE_Y = CENTER - 1.5            # the three openings share one line
FEATURE_X = (CENTER - 1.9, CENTER, CENTER + 1.9)

GRATING_LINES = 6                   # small 1D grating on the top layer
GRATING_PITCH = 0.40
GRATING_WIDTH = 0.20
GRATING_LENGTH = 2.6
GRATING_X0 = CENTER - GRATING_LENGTH / 2
GRATING_Y0 = CENTER + 1.0


def build_steps():
    """Return snapshots with three exact, independently filled hole shapes."""
    steps = []
    wafer = Wafer(size=DIAMETER, shape="circle", substrate="Si",
                  thickness=1.0, notch="V")
    steps.append(("1  circular wafer", "Wafer(size=diameter, shape=\"circle\", notch=\"V\")",
                  deepcopy(wafer)))

    wafer.add_layer("SiO2", 0.30, label="gate oxide")
    steps.append(("2  inherited film shape", "add_layer(...)  # circular blanket",
                  deepcopy(wafer)))

    wafer.add_multilayer([("Si3N4", 0.22), ("SiO2", 0.18)], repeats=2)
    steps.append(("3  repeated stack", "add_multilayer(layers, repeats=2)",
                  deepcopy(wafer)))

    # One line, one pitch: the three shapes differ, their placement does not.
    rectangle = wafer.etch(
        Rectangle(center=(FEATURE_X[0], FEATURE_Y), size=(1.30, 0.88)),
        depth=0.70, name="rectangular trench")
    circle = wafer.etch(
        Circle(center=(FEATURE_X[1], FEATURE_Y), radius=0.52),
        name="circular via")
    ellipse = wafer.etch(
        Ellipse(center=(FEATURE_X[2], FEATURE_Y), radii=(0.74, 0.40),
                rotation=-25),
        depth=0.95, name="elliptical contact")
    steps.append(("4  boolean etch", "etch(Rectangle / Circle / Ellipse)",
                  deepcopy(wafer)))

    wafer.fill(rectangle, "Cu", name="Cu trench fill")
    wafer.fill(circle, "W", name="W via fill")
    wafer.fill(ellipse, "SiP", overfill=0.42, name="raised Si:P contact")
    steps.append(("5  exact-shape fill",
                  "fill(rect, Cu)  fill(circle, W)  fill(ellipse, Si:P)",
                  deepcopy(wafer)))

    # A small 1D grating: equal lines at a constant pitch, which is what a
    # patterned top layer usually is.
    for line in range(GRATING_LINES):
        wafer.add_pad("W", GRATING_X0, GRATING_Y0 + line * GRATING_PITCH,
                      GRATING_LENGTH, GRATING_WIDTH, 0.26,
                      name=f"grating line {line + 1}")
    steps.append(("6  1D grating on top",
                  "add_pad(...) per line at a constant pitch",
                  deepcopy(wafer)))
    return steps


def render_snapshot(wafer):
    """Use one camera and the full solid renderer for all process states."""
    scene = wafer.model(backend="solid")
    return scene.render_array(window=(1100, 820), zoom=1.14,
                              azimuth=-30.0, elevation=-17.0,
                              transparent=True)


def make_figure():
    plt.rcParams.update(PLOT_STYLE)
    fig, axes = plt.subplots(3, 2, figsize=(6.3, 7.1))
    fig.subplots_adjust(left=0.025, right=0.985, top=0.90, bottom=0.06,
                        hspace=0.25, wspace=0.08)
    fig.suptitle("Boolean-solid process DSL feature tour", fontsize=11.6,
                 color=C_SLATE, weight="bold")
    fig.text(0.5, 0.925,
             "One readable run sheet; topology-changing steps select the "
             "trimesh/manifold3d backend",
             fontsize=7.8, color=C_GREY, ha="center")

    for ax, (title, method, wafer) in zip(axes.flat, build_steps()):
        ax.set_axis_off()
        ax.imshow(render_snapshot(wafer))
        ax.text(0.02, 0.97, title, transform=ax.transAxes, fontsize=9.0,
                color=C_SLATE, weight="bold", va="top")
        ax.text(0.02, 0.035, method, transform=ax.transAxes, fontsize=7.0,
                color=C_GREY, family="monospace", va="bottom")

    fig.text(0.5, 0.015,
             "Circular wafer and films are true cylinders. Rectangle, circle "
             "and rotated-ellipse fills reuse their void geometry.",
             fontsize=7.0, color=C_GREY, ha="center")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "dsl_feature_tour"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem


def main():
    stem = make_figure()
    print(f"wrote {stem}.pdf (+ .png)")


if __name__ == "__main__":
    main()
