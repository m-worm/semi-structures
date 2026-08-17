"""Tests for the shared tool layer, the CLI, and the MCP binding.

The tool layer and the CLI carry no MCP dependency, so they are always
tested; the binding tests skip when the ``mcp`` extra is absent.
"""
import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from semi_structures import cli, mcp_tools
from semi_structures.mcp_tools import ToolError

HAS_MCP = importlib.util.find_spec("mcp") is not None
HAS_SOLID = all(importlib.util.find_spec(name) is not None
                for name in ("pyvista", "trimesh"))


class SandboxTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        os.environ["SEMI_STRUCTURES_MCP_OUTPUT"] = self.directory

    def tearDown(self):
        os.environ.pop("SEMI_STRUCTURES_MCP_OUTPUT", None)

    def test_output_directory_follows_the_environment(self):
        self.assertEqual(mcp_tools.output_directory(),
                         Path(self.directory).resolve())

    def test_filenames_that_escape_or_surprise_are_refused(self):
        for bad in ("../escape.png", "sub/dir.png", "sub\\dir.png",
                    "..\\escape.png", "", "no-suffix", "figure.exe",
                    "figure.py", ".hidden.png", "a" * 80 + ".png"):
            with self.subTest(filename=bad):
                with self.assertRaises(ToolError):
                    mcp_tools.resolve_output_path(bad)

    def test_a_good_filename_lands_in_the_sandbox(self):
        path = mcp_tools.resolve_output_path("figure_1.png")
        self.assertEqual(path.parent, Path(self.directory).resolve())
        self.assertEqual(path.name, "figure_1.png")


class MaterialToolTests(unittest.TestCase):
    def test_list_and_get(self):
        listing = mcp_tools.list_materials()
        self.assertEqual(listing["count"], len(listing["materials"]))
        self.assertGreater(listing["count"], 20)
        names = {m["name"] for m in listing["materials"]}
        self.assertIn("Si", names)
        self.assertIn("sapphire", names)

        entry = mcp_tools.get_material("SiO2")
        self.assertEqual(entry["hex"], "#F2EAD8")
        self.assertEqual(entry["alpha"], 1.0)
        self.assertIn("dielectric", entry["family"])
        self.assertLess(mcp_tools.get_material("sapphire")["alpha"], 1.0)

    def test_unknown_material_is_refused_with_a_hint(self):
        with self.assertRaises(ToolError) as caught:
            mcp_tools.get_material("sio2")
        self.assertIn("SiO2", str(caught.exception))


class PatternToolTests(unittest.TestCase):
    def test_every_bundled_pattern_is_valid_and_round_trips(self):
        for item in mcp_tools.list_examples()["examples"]:
            with self.subTest(pattern=item["name"]):
                document = mcp_tools.get_example(item["name"])["document"]
                report = mcp_tools.validate_process(document)
                self.assertTrue(report["valid"], report["errors"])
                self.assertIn(report["backend"], ("vector", "solid"))
                # normalizing twice is stable
                self.assertEqual(
                    mcp_tools.validate_process(report["normalized"])
                    ["normalized"], report["normalized"])

    def test_unknown_pattern_is_refused(self):
        with self.assertRaises(ToolError):
            mcp_tools.get_example("nope")


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.document = mcp_tools.get_example("damascene")["document"]

    def test_a_bad_document_reports_rather_than_raises(self):
        report = mcp_tools.validate_process({"format": "wrong"})
        self.assertFalse(report["valid"])
        self.assertTrue(report["errors"])
        self.assertIsNone(report["normalized"])

    def test_unknown_verbs_and_private_methods_are_refused(self):
        for verb in ("vaporize", "_record_layer", "to_json"):
            document = dict(self.document,
                            operations=[{"op": verb}])
            with self.subTest(verb=verb):
                self.assertFalse(
                    mcp_tools.validate_process(document)["valid"])

    def test_oversized_documents_are_refused(self):
        huge = dict(self.document, operations=[
            {"op": "add_layer", "material": "SiO2", "thickness": 0.1}
        ] * (mcp_tools.MAX_OPERATIONS + 1))
        report = mcp_tools.validate_process(huge)
        self.assertFalse(report["valid"])
        self.assertIn("limit", report["errors"][0])

        many = dict(self.document, operations=[
            {"op": "add_multilayer", "layers": [["SiO2", 0.1]],
             "repeats": mcp_tools.MAX_REPEATS + 1}])
        self.assertFalse(mcp_tools.validate_process(many)["valid"])

    def test_inspect_reports_the_structure(self):
        report = mcp_tools.inspect_structure(self.document)
        self.assertEqual(report["backend"], "vector")
        self.assertFalse(report["requires_solid"])
        self.assertEqual(report["footprint"]["x"], [0.0, 10.0])
        self.assertEqual(report["counts"]["etches"], 1)
        self.assertEqual(report["history"][-1], "strip")
        self.assertTrue(any(f["name"] == "Cu" for f in report["features"]))


class RenderToolTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        os.environ["SEMI_STRUCTURES_MCP_OUTPUT"] = self.directory
        self.document = mcp_tools.get_example("damascene")["document"]

    def tearDown(self):
        os.environ.pop("SEMI_STRUCTURES_MCP_OUTPUT", None)

    def test_render_writes_into_the_sandbox(self):
        result = mcp_tools.render_structure(self.document, "cell.png",
                                            view="section", dpi=80)
        self.assertEqual(Path(result["path"]).parent,
                         Path(self.directory).resolve())
        self.assertGreater(result["bytes"], 0)
        self.assertEqual(result["backend"], "vector")

    def test_render_to_path_is_free_but_still_checks_the_suffix(self):
        target = Path(self.directory) / "elsewhere.pdf"
        result = mcp_tools.render_to_path(self.document, target,
                                          view="section", dpi=80)
        self.assertTrue(Path(result["path"]).exists())
        with self.assertRaises(ToolError):
            mcp_tools.render_to_path(self.document, target.with_suffix(".exe"))

    def test_absurd_image_requests_are_refused(self):
        for kwargs in ({"dpi": 100_000}, {"print_width_in": 500},
                       {"print_width_in": 19, "dpi": 1100}):
            with self.subTest(**kwargs):
                with self.assertRaises(ToolError):
                    mcp_tools.render_structure(self.document, "big.png",
                                               **kwargs)


class ExportTests(unittest.TestCase):
    def test_exported_source_runs_and_rebuilds_the_model(self):
        document = mcp_tools.get_example("damascene")["document"]
        source = mcp_tools.export_python(document)["source"]
        self.assertIn("from semi_structures import Wafer, Rectangle", source)
        self.assertIn("w = Wafer(size=(10.0, 6.0)", source)

        # Execute it (minus the trailing render) and compare to the document.
        body = source.split('w.render(')[0]
        namespace = {}
        exec(compile(body, "<exported>", "exec"), namespace)   # noqa: S102
        self.assertEqual(namespace["w"].to_dict(), document)

    def test_every_pattern_exports_runnable_source(self):
        for item in mcp_tools.list_examples()["examples"]:
            with self.subTest(pattern=item["name"]):
                document = mcp_tools.get_example(item["name"])["document"]
                source = mcp_tools.export_python(document)["source"]
                body = source.split('w.render(')[0]
                namespace = {}
                exec(compile(body, "<exported>", "exec"), namespace)  # noqa: S102
                self.assertEqual(namespace["w"].to_dict(), document)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_materials_json_and_table(self):
        code, out, _ = self.run_cli("materials", "Si")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["hex"], "#ADD8E6")

        code, out, _ = self.run_cli("materials", "--table", "--family", "metal")
        self.assertEqual(code, 0)
        self.assertIn("Cu", out)
        self.assertIn("rho_e", out)

    def test_example_validate_inspect_and_export(self):
        code, out, _ = self.run_cli("example", "damascene")
        self.assertEqual(code, 0)
        document = json.loads(out)
        path = self.directory / "cell.json"
        path.write_text(json.dumps(document), encoding="utf-8")

        code, out, _ = self.run_cli("validate", str(path))
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["valid"])

        code, out, _ = self.run_cli("inspect", str(path))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["backend"], "vector")

        code, out, _ = self.run_cli("export", str(path))
        self.assertEqual(code, 0)
        self.assertIn("w = Wafer(", out)

    def test_render_writes_the_requested_file(self):
        code, out, _ = self.run_cli("example", "damascene")
        path = self.directory / "cell.json"
        path.write_text(out, encoding="utf-8")
        target = self.directory / "figure.png"
        code, out, _ = self.run_cli("render", str(path), "-o", str(target),
                                    "--view", "section", "--dpi", "80")
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())
        self.assertEqual(json.loads(out)["backend"], "vector")

    def test_invalid_document_exits_nonzero(self):
        path = self.directory / "bad.json"
        path.write_text('{"format": "nope"}', encoding="utf-8")
        code, _, _ = self.run_cli("validate", str(path), "--quiet")
        self.assertEqual(code, 1)

    def test_unreadable_and_malformed_input_are_reported(self):
        code, _, err = self.run_cli("inspect", str(self.directory / "gone.json"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

        path = self.directory / "broken.json"
        path.write_text("{not json", encoding="utf-8")
        code, _, err = self.run_cli("inspect", str(path))
        self.assertEqual(code, 2)
        self.assertIn("invalid JSON", err)


@unittest.skipUnless(HAS_MCP, "the 'mcp' extra is not installed")
class ServerBindingTests(unittest.TestCase):
    def test_every_tool_is_registered_with_a_schema(self):
        import asyncio

        from semi_structures.mcp_server import build_server

        server = build_server()
        tools = asyncio.run(server.list_tools())
        names = {tool.name for tool in tools}
        self.assertEqual(
            names, {function.__name__ for function in mcp_tools.TOOLS})

        by_name = {tool.name: tool for tool in tools}
        for tool in tools:
            self.assertTrue((tool.description or "").strip(),
                            f"{tool.name} has no description")

        def schema_of(tool):
            return (getattr(tool, "input_schema", None)
                    or getattr(tool, "inputSchema", None) or {})

        # render_structure's parameters must be spelled out, because the
        # schema is the contract an MCP client sees.
        render = schema_of(by_name["render_structure"])
        self.assertEqual(set(render.get("required", [])),
                         {"document", "filename"})
        for name in ("backend", "view", "labels", "print_width_in", "dpi"):
            self.assertIn(name, render.get("properties", {}))
        self.assertEqual(schema_of(by_name["get_material"]).get("required"),
                         ["name"])


if __name__ == "__main__":
    unittest.main()
