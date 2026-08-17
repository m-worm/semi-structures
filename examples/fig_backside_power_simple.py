"""fig_backside_power_simple.py -- backside power delivery, the simple block.

A stylised companion to fig_backside_power_delivery.py, authored from a
supplied "simplified backside power" illustration: one die block with the
signal layers exploded above it as a stack of plates, a thinned transistor
layer with a few transistor pads, a backside power-delivery block below
(power metals in dielectric), a single nano-TSV standing in a stepped cut
so it can be seen running from the top plate down to the backside metal,
and a solder-ball array underneath. The reference supplied only the
composition, viewpoint and the three callouts (signal layers, power,
nTSV); geometry, dimensions and colors are new, and the image is not
redistributed (provenance in ``examples/REFERENCES.md``).

Material language (the book's palette): Cu for signal plates and backside
power metals, SiO2 for the power-block dielectric, Si for the thinned
device layer, TiN for the transistor pads, W for the nTSV, Sn solder balls.
The reference's orange/grey/dark-background scheme is a presentation
override available through ``Scene.render(background=, edge_color=)`` and
raw hex fills, kept out of the default figure on purpose.

Outputs: ../docs/figures/backside_power_simple.png and .pdf
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from semi_structures.solid import C_SLATE, Scene
from semi_structures.style import PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

# ---- layout (model units) ---------------------------------------------------
LX, LY = 12.0, 10.0                     # die footprint
Z_CU0, T_CU = 0.0, 0.30                 # backside metal sheets
Z_SI, T_SI = 3.0, 0.60                  # thinned device layer
STEP_X, Z_STEP = 6.8, 1.9               # step: for x > STEP_X the block stops
PLATE = ((0.6, 0.6), (LX - 1.2, LY - 1.2))          # signal plate footprint
PLATE_Z = (4.4, 5.15, 5.9, 6.65)        # thin plates
TOP_Z, TOP_T = 7.4, 0.55                # thicker top plate
TSV = (STEP_X + 0.7, 2.6, 0.22)         # (x, y, r) of the nano-TSV
BALL_R, BALL_PITCH = 0.62, 1.75


def build(labels=True):
    s = Scene()

    # Solder balls under the die.
    s.sphere_array((0.9, LX - 0.9), (0.75, LY - 0.9), BALL_PITCH,
                   z=-BALL_R, r=BALL_R, material="Sn")

    # Backside power-delivery block: Cu sheets in SiO2, then thinned Si.
    # The part right of STEP_X is cut down to the second Cu sheet, so the
    # nano-TSV can be seen standing on it and running up to the plates.
    parts = []
    parts.append(s.box((0, 0, Z_CU0), (LX, LY, T_CU), "Cu"))
    parts.append(s.box((0, 0, Z_CU0 + T_CU), (LX, LY, 1.6 - T_CU), "SiO2"))
    parts.append(s.box((0, 0, 1.6), (LX, LY, T_CU), "Cu"))
    parts.append(s.box((0, 0, 1.6 + T_CU), (LX, LY, Z_SI - 1.6 - T_CU),
                       "SiO2"))
    parts.append(s.box((0, 0, Z_SI), (LX, LY, T_SI), "Si"))
    s.drill_rect(STEP_X, -1.0, LX, LY + 2.0, z0=Z_STEP, z1=Z_SI + T_SI + 1,
                 only=parts)

    # Transistor pads on the device layer (left, taller part only).
    for x in (1.0, 2.6, 4.2):
        for y in (1.2, 3.0):
            s.box((x, y, Z_SI + T_SI), (1.1, 0.7, 0.16), "TiN")

    # Signal layers: four thin Cu plates and a thicker top plate, exploded.
    # The thin plates carry a slot from the front edge to the nano-TSV so
    # the via stays visible where it runs up through them.
    (px, py), (pdx, pdy) = PLATE
    tx, ty, tr = TSV
    thin = [s.box((px, py, z), (pdx, pdy, 0.24), "Cu") for z in PLATE_Z]
    s.drill_rect(tx - 2.2 * tr, -1.0, 4.4 * tr, ty + 1.0 + 2.2 * tr,
                 only=thin)
    s.box((px, py, TOP_Z), (pdx, pdy, TOP_T), "Cu")

    # The nano-TSV: W, from the backside metal to the top plate.
    s.cylinder((tx, ty), Z_CU0 + T_CU, tr, TOP_Z - (Z_CU0 + T_CU), "W")

    if not labels:
        return s
    # ---- callouts (points at the 6.3 in print width used in main) --------
    s.text2d("Backside power delivery, simplified", position="upper_left",
             size=10.0)
    # Stick-and-ball callouts, leaders in the text color rather than the
    # paler palette default.
    call = dict(size=8.2, marker="dot", line_color=C_SLATE, line_width=0.8)
    right = dict(justify="right", **call)
    s.label("signal layers (Cu)",
            anchor=(px + 0.5 * pdx, py + pdy, TOP_Z + TOP_T),
            via=(0.78, 0.13), position=(0.97, 0.13), **right)
    s.label("transistors on thinned Si",
            anchor=(3.15, 1.2, Z_SI + T_SI + 0.16),
            via=(0.28, 0.42), position=(0.03, 0.42), **call)
    s.label("backside power (Cu in SiO$_2$)".replace("$_2$", "2"),
            anchor=(LX, 0.4 * LY, 1.75),
            via=(0.70, 0.62), position=(0.97, 0.62), **right)
    s.label("nTSV (W)", anchor=(tx, ty - tr, Z_SI + T_SI + 0.4),
            via=(0.80, 0.46), position=(0.97, 0.46), **right)
    s.label("solder balls (Sn)", anchor=(2.75, 1.0 - 0.3, -BALL_R),
            via=(0.20, 0.80), position=(0.03, 0.80), **call)
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "backside_power_simple.png"
    print_width, aspect = 6.3, 0.72
    # Camera from -y (a little +x): the y=0 face is frontal with x running
    # left to right, the stepped +x face at the right, ~25 deg above the
    # horizon -- the viewpoint of the reference.
    build().render(str(png), print_width_in=print_width, aspect=aspect,
                   zoom=1.05, azimuth=-115.0, elevation=-10.0)

    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(print_width, print_width * aspect))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(mpimg.imread(png))
    ax.set_axis_off()
    fig.savefig(OUT / "backside_power_simple.pdf")
    plt.close(fig)
    print(f"wrote {png} and {OUT / 'backside_power_simple.pdf'}")


if __name__ == "__main__":
    main()
