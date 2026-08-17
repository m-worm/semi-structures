"""Semiconductor structure drawing and process-flow tools.

The lightweight vector/process API is available from the package root.
Import ``Scene`` from :mod:`semi_structures.solid` when the optional solid
dependencies are installed.
"""

from .iso import Box, Pillar, draw_scene, iso, slab_with_holes
from .process import (
    Circle, Ellipse, EtchFeature, FillFeature, Layer, Rectangle,
    RegionFeature, Wafer, hex_lattice, mm, nm, shape_bounds, square_lattice, um,
)
from .section import draw_section
from .serialize import (wafer_from_dict, wafer_from_json, wafer_to_dict,
                        wafer_to_json)
from .style import (FIGSIZES, LINE_PALETTE, MATERIAL, MATERIAL_ALPHA,
                    PLOT_STYLE, alloy_color, alpha_for, doped)

__version__ = "0.2.0"

__all__ = [
    "Box",
    "Circle",
    "Ellipse",
    "EtchFeature",
    "FIGSIZES",
    "FillFeature",
    "LINE_PALETTE",
    "Layer",
    "MATERIAL",
    "MATERIAL_ALPHA",
    "PLOT_STYLE",
    "Pillar",
    "Rectangle",
    "RegionFeature",
    "Wafer",
    "alloy_color",
    "alpha_for",
    "doped",
    "draw_scene",
    "draw_section",
    "hex_lattice",
    "iso",
    "mm",
    "nm",
    "shape_bounds",
    "slab_with_holes",
    "square_lattice",
    "um",
    "wafer_from_dict",
    "wafer_from_json",
    "wafer_to_dict",
    "wafer_to_json",
]
