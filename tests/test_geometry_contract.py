import json
from pathlib import Path
import unittest

from core.geometry_contract import GeometryContractError, build_layout, inspect_instance


FIXTURE = Path(__file__).with_name("shelf_instance.json")


class GeometryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_double_row_counts_and_levels(self):
        layout = build_layout(self.instance)
        self.assertEqual(layout.rows, ((0.0, 1000.0), (1200.0, 2200.0)))
        self.assertEqual(layout.frame_x, (0.0, 2300.0, 4600.0, 6900.0))
        self.assertEqual(
            layout.beam_z,
            (300.0, 1566.6666666666667, 2833.3333333333335, 4100.0),
        )
        self.assertEqual(
            layout.counts,
            {
                "columns": 16,
                "base_plates": 16,
                "beams": 48,
                "panels": 24,
                "braces": 28,
                "spacers": 0,
            },
        )
        self.assertEqual(layout.planned_counts["spacers"], 16)

    def test_missing_or_invalid_dimensions_are_rejected(self):
        data = json.loads(json.dumps(self.instance))
        data["global_constraints"]["height"] = 0
        with self.assertRaises(GeometryContractError):
            build_layout(data)

        data = json.loads(json.dumps(self.instance))
        data["components"] = [c for c in data["components"] if c["type"] != "beam"]
        with self.assertRaises(GeometryContractError):
            build_layout(data)

    def test_single_row_is_a_real_variant(self):
        data = json.loads(json.dumps(self.instance))
        data["global_constraints"]["is_double_row"] = False
        layout = build_layout(data)
        self.assertEqual(len(layout.rows), 1)
        self.assertEqual(layout.counts["spacers"], 0)
        self.assertEqual(layout.planned_counts["spacers"], 0)
        self.assertEqual(layout.counts["columns"], 8)

    def test_inspection_result_is_ui_safe(self):
        result = inspect_instance(self.instance)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["layout"]["counts"]["panels"], 24)
        invalid = json.loads(json.dumps(self.instance))
        invalid["global_constraints"]["width"] = -1
        self.assertEqual(inspect_instance(invalid)["status"], "error")


if __name__ == "__main__":
    unittest.main()
