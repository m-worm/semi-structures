"""fig_serialization_roundtrip.py -- saving a process model as JSON.

A model is built with the DSL, written to a JSON document, read back, and
drawn again. What the document stores is the *recipe* -- the ordered verb
calls with their arguments -- not the derived geometry, so replaying it
rebuilds every layer, hole and fill. The two renderings are compared by
SHA-256 of their PNG bytes, and the figure prints the result: the reproduced
model is not merely similar, it is the same picture.

The document is also the interchange format an MCP server or any other
non-Python client would exchange, and the input `export_python` would turn
back into a script.

Outputs: ../docs/figures/serialization_roundtrip.pdf (+ .png)
"""
from __future__ import annotations

import hashlib
import io
import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from semi_structures import Rectangle, Wafer
from semi_structures.style import C_GREY, C_SLATE, PLOT_STYLE

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "figures"


def build():
    """A small damascene flow: oxide, hard mask, trench, Cu fill, strip."""
    w = Wafer(size=(10.0, 6.0), substrate="Si", thickness=2.0, name="Si wafer")
    oxide = w.add_layer("SiO2", 1.2, name="SiO$_2$")
    w.add_layer("Si3N4", 0.5, name="hard mask")
    trench = w.etch(Rectangle.from_corner(3.0, 0.0, 4.0, 6.0), stop_on=oxide,
                    name="trench")
    w.fill(trench, "Cu", overfill=0.0, name="Cu")
    w.strip("hard mask")
    return w


def digest(wafer):
    """SHA-256 of this model's rendered pixels."""
    figure, axes = plt.subplots(figsize=(3.0, 1.6))
    wafer.render(ax=axes, view="section", labels=False)
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=150)
    plt.close(figure)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def compact_document(document, width=52):
    """The document as JSON, one operation per entry, wrapped to fit.

    ``json.dumps(indent=...)` puts every list element on its own line, which
    is unreadable at figure scale; this keeps genuine JSON but folds each
    operation onto as few lines as it needs.
    """
    def fold(text, indent=""):
        return [indent + part for part in
                textwrap.wrap(text, width=width - len(indent),
                              subsequent_indent="   ",
                              break_long_words=False)]

    parsed = json.loads(document)
    lines = fold(f'"format": "{parsed["format"]}", '
                 f'"version": {parsed["version"]},')
    lines += fold('"wafer": ' + json.dumps(parsed["wafer"],
                                           separators=(", ", ": ")) + ",")
    lines.append('"operations": [')
    for operation in parsed["operations"]:
        lines += fold(json.dumps(operation, separators=(", ", ": ")), "  ")
    lines.append("]")
    return "\n".join(lines)


def make_figure():
    original = build()
    document = original.to_json()
    restored = Wafer.from_json(document)
    same = digest(original) == digest(restored)

    plt.rcParams.update(PLOT_STYLE)
    fig = plt.figure(figsize=(6.3, 2.95))

    fig.text(0.015, 0.945, "A process model round-trips through JSON",
             fontsize=10.0, color=C_SLATE, weight="bold", va="baseline")

    # ---- left: the document -------------------------------------------------
    ax_json = fig.add_axes([0.015, 0.12, 0.50, 0.76])
    ax_json.set_axis_off()
    ax_json.text(0.0, 1.0, "cell.json", fontsize=8.0, family="monospace",
                 color=C_GREY, va="top", ha="left")
    ax_json.text(0.0, 0.905, compact_document(document), fontsize=7.0,
                 family="monospace", color=C_SLATE, va="top", ha="left",
                 linespacing=1.30)

    # ---- right: the two renderings -----------------------------------------
    limits = None
    for index, (wafer, title) in enumerate((
            (original, "built with the DSL"),
            (restored, "rebuilt from cell.json"))):
        axes = fig.add_axes([0.60, 0.495 - 0.400 * index, 0.385, 0.30])
        # Labelling only the materials keeps the two leaders from the trench
        # and its fill, which anchor at nearly the same point, out of the way.
        wafer.render(ax=axes, view="section",
                     labels=["Si wafer", "SiO$_2$", "Cu"], label_size=7.0,
                     label_marker="dot")
        axes.set_xlim(-5.2, 10.6)
        # The panels are the same picture, so pin the second to the first's
        # vertical limits rather than letting each autoscale to its callouts.
        if limits is None:
            limits = axes.get_ylim()
        else:
            axes.set_ylim(limits)
        axes.text(0.62, 1.06, title, transform=axes.transAxes, fontsize=8.3,
                  color=C_SLATE, weight="bold", ha="center", va="bottom")

    verdict = ("identical pixels: SHA-256 of the two renderings agree"
               if same else "RENDERINGS DIFFER")
    fig.text(0.795, 0.045, verdict, fontsize=7.2, color=C_GREY, ha="center")

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / "serialization_roundtrip"
    fig.savefig(f"{stem}.pdf")
    fig.savefig(f"{stem}.png", dpi=300)
    plt.close(fig)
    return stem, same


def main():
    stem, same = make_figure()
    if not same:
        raise SystemExit("round-trip renderings differ")
    print(f"wrote {stem}.pdf (+ .png); round-trip renders identical pixels")


if __name__ == "__main__":
    main()
