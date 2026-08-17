"""Regenerate every documentation figure in a deterministic order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXAMPLES = (
    "fig_hero_banner.py",
    "fig_material_palette.py",
    "fig_chart_style_guide.py",
    "fig_dsl_feature_tour.py",
    "fig_rotated_ellipses.py",
    "fig_wafer_notch.py",
    "fig_litho_flow.py",
    "fig_litho_flow_3d.py",
    "fig_serialization_roundtrip.py",
    "fig_stack_gallery.py",
    "fig_film_stress_bow.py",
    "fig_transistor_evolution.py",
    "fig_transistor_solid.py",
    "fig_memory_generations.py",
    "fig_dram3d.py",
    "fig_nand3d.py",
    "fig_nand_solid.py",
    "fig_nand_stack_break.py",
    "fig_optoelectronic_devices.py",
    "fig_sic_power_devices.py",
    "fig_backside_power_delivery.py",
    "fig_backside_power_simple.py",
    "fig_hbm_labeled.py",
    # authored from reference images (see examples/REFERENCES.md)
    "fig_chiplet_package.py",
    "fig_gpu_cowos_exploded.py",
    "fig_gpu_cowos_assembled.py",
    "fig_transistor_evolution_rolecolor.py",
    "fig_dram3d_reference_colors.py",
    "fig_dram3d_capacitor_schematics.py",
)


def main() -> None:
    for name in EXAMPLES:
        print(f"Generating {name}", flush=True)
        subprocess.run([sys.executable, str(HERE / name)], check=True)


if __name__ == "__main__":
    main()
