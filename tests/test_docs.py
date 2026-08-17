"""The documentation's Python examples must actually run.

Every ```python block in a markdown file is executed. Blocks within one file
share a namespace and run in order, because a document is a narrative: a
later block may legitimately continue from an earlier one. Anything that is
deliberately not runnable -- proposed API, shell transcripts -- belongs in a
```text block instead, which is the convention this test enforces.

This is what stops a snippet from rotting when a signature changes.
"""
import os
import re
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
BLOCK = re.compile(r"```python\n(.*?)```", re.S)


def documents():
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        yield path


class DocumentationExampleTests(unittest.TestCase):
    def test_every_python_block_runs(self):
        checked = 0
        for path in documents():
            blocks = BLOCK.findall(path.read_text(encoding="utf-8"))
            if not blocks:
                continue
            # A scratch working directory shaped like the repository, so a
            # snippet may write where the documentation says figures go.
            with tempfile.TemporaryDirectory() as folder:
                (Path(folder) / "docs" / "figures").mkdir(parents=True)
                previous = os.getcwd()
                os.chdir(folder)
                namespace = {"__name__": "__doc__"}
                try:
                    for index, code in enumerate(blocks):
                        with self.subTest(document=str(
                                path.relative_to(ROOT)), block=index):
                            try:
                                exec(compile(code, f"{path.name}#{index}",
                                             "exec"), namespace)   # noqa: S102
                            except Exception as error:   # noqa: BLE001
                                self.fail(
                                    f"{path.relative_to(ROOT)} block {index} "
                                    f"failed: {type(error).__name__}: {error}\n"
                                    f"first line: "
                                    f"{code.strip().splitlines()[0][:70]}")
                            checked += 1
                finally:
                    os.chdir(previous)
                    plt.close("all")
        self.assertGreater(checked, 5, "no documentation examples were found")


if __name__ == "__main__":
    unittest.main()
