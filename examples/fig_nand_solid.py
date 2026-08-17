"""fig_nand_solid.py -- 3D-NAND with true drilled plates and shells.

The SanDisk-style concept rebuilt on the semi_structures.solid backend: W word-line
plates with genuinely drilled circular holes, channel pillars as real
concentric tubes (blocking SiO2 / Si3N4 trap / tunnel SiO2 / poly-Si
channel / SiO2 core), one pillar telescoped to reveal the stack. Colors
are semi_structures.style materials; render is parallel-projection with slate
feature edges on white.

Outputs: ../docs/figures/nand3d_solid.png and nand3d_cutaway.png
"""
from __future__ import annotations

from pathlib import Path

from semi_structures.solid import Scene

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"

SHELLS = [                 # (material, r_out, r_in); solid core last
    ("SiO2", 1.00, 0.80), ("Si3N4", 0.80, 0.60), ("SiO2", 0.60, 0.42),
    ("Si", 0.42, 0.26),
]
PLATE_Z = (0.7, 2.5, 4.3)
PLATE_T = 1.0
TOP = PLATE_Z[-1] + PLATE_T
CENTERS = [(3.1, 4.9, False), (6.5, 4.9, False), (6.5, 2.1, False),
           (3.1, 2.1, True)]


def build():
    s = Scene()
    s.box((0, 0, 0), (10.6, 7.2, 0.45), "Si")
    plates = [s.box((0.2, 0.2, z0), (10.2, 6.8, PLATE_T), "W")
              for z0 in PLATE_Z]

    for cx, cy, _ in CENTERS:
        s.drill_hole(cx, cy, 1.06, only=plates)

    for cx, cy, telescope in CENTERS:
        for i, (mat, r_out, r_in) in enumerate(SHELLS):
            head = 0.30 + (0.55 * (i + 1) if telescope else 0.0)
            s.tube((cx, cy), 0.45, r_out, r_in, TOP - 0.45 + head, mat)
        core_head = 0.30 + (0.55 * 5 if telescope else 0.0)
        s.cylinder((cx, cy), 0.45, 0.26, TOP - 0.45 + core_head, "SiO2")
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "nand3d_solid.png"
    build().render(str(path), zoom=1.2, azimuth=-30.0, elevation=-16.0)
    print(f"wrote {path}")

    # Quarter-section through a channel pillar. Capped cut faces expose
    # the shell sequence through every drilled word-line plate.
    s = build()
    s.cutaway(x=6.5, y=4.9)
    path = OUT / "nand3d_cutaway.png"
    s.render(str(path), zoom=1.2, azimuth=-30.0, elevation=-16.0)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
