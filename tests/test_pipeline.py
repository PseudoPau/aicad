import unittest
from pathlib import Path

from core.pipeline import build_preview, load_instance, validate_instance
from core.geometry_contract import build_layout


ROOT = Path(__file__).resolve().parents[1]


class PipelineFixtureTests(unittest.TestCase):
    def setUp(self):
        self.instance = load_instance(ROOT / "tests" / "shelf_instance.json")

    def test_fixture_is_semantically_valid(self):
        report = validate_instance(self.instance, ROOT / "schema" / "assembly_schema.json")
        self.assertTrue(report["ok"], report)

    def test_double_row_counts_and_diagonal_braces(self):
        preview = build_preview(self.instance)
        self.assertTrue(preview["ok"], preview)
        self.assertEqual(preview["counts"]["column"], 16)
        self.assertEqual(preview["counts"]["beam"], 48)
        self.assertEqual(preview["counts"]["panel"], 24)
        brace = next(item for item in preview["items"] if item["kind"] == "bracing")
        self.assertNotEqual(brace["start"][1], brace["end"][1])
        self.assertNotEqual(brace["start"][2], brace["end"][2])

    def test_preview_counts_match_domain_contract(self):
        preview = build_preview(self.instance)
        layout = build_layout(self.instance)
        self.assertEqual(preview["counts"]["column"], layout.counts["columns"])
        self.assertEqual(preview["counts"]["base_plate"], layout.counts["base_plates"])
        self.assertEqual(preview["counts"]["beam"], layout.counts["beams"])
        self.assertEqual(preview["counts"]["panel"], layout.counts["panels"])
        self.assertEqual(preview["counts"]["bracing"], layout.counts["braces"])

    def test_invalid_negative_dimension_is_rejected(self):
        self.instance["global_constraints"]["width"] = -1
        report = validate_instance(self.instance, ROOT / "schema" / "assembly_schema.json")
        self.assertFalse(report["ok"])
        self.assertTrue(any("width" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
