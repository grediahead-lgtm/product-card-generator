import csv
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

from card_gen.__main__ import main  # noqa: E402
from card_gen.generate import build_card, check, fill, pick, run  # noqa: E402

with open(os.path.join(ROOT, "examples", "config.json"), encoding="utf-8") as f:
    CFG = json.load(f)
with open(os.path.join(ROOT, "examples", "products.csv"), encoding="utf-8") as f:
    ROWS = list(csv.DictReader(f))


class FillTests(unittest.TestCase):
    def test_optional_part_dropped_when_empty(self):
        self.assertEqual(fill("Bed[ {color}][ {size}]", {"color": "", "size": "40x30"}), ("Bed 40x30", []))
        self.assertEqual(fill("Bed[ {color}]", {"color": "grey"}), ("Bed grey", []))

    def test_missing_required_is_reported_not_invented(self):
        text, missing = fill("{type} {brand}", {"type": "Bed"})
        self.assertEqual((text, missing), ("Bed", ["brand"]))

    def test_pick_is_deterministic_and_varies(self):
        v = ["a", "b", "c", "d"]
        self.assertEqual(pick(v, "x"), pick(v, "x"))
        self.assertGreater(len({pick(v, "sku%d" % i) for i in range(30)}), 1)


class CardTests(unittest.TestCase):
    def test_sentences_with_missing_data_are_left_out(self):
        title, desc, missing = build_card(ROWS[1], CFG["languages"]["uk"], "A2")  # no colour, no material
        self.assertNotIn("Колір", desc)
        self.assertNotIn("Матеріал", desc)
        self.assertIn("Розмір: 26x30x16.", desc)
        self.assertIn("color", missing)

    def test_no_empty_placeholders_or_none_in_output(self):
        for r in ROWS:
            for lc in CFG["languages"].values():
                title, desc, _ = build_card(r, lc, r["sku"])
                self.assertNotIn("{", title + desc)
                self.assertNotIn("None", title + desc)


class CheckTests(unittest.TestCase):
    LIM = {"title_min": 10, "title_max": 20, "desc_min": 30, "desc_max": 60}

    def test_lengths(self):
        self.assertTrue(any("max 20" in x for x in check("x" * 21, "d" * 40, self.LIM)))
        self.assertTrue(any("min 30" in x for x in check("title long enough", "short", self.LIM)))

    def test_risky_claims(self):
        got = check("Найкращий лежак", "Лучший выбор, 100% гарантія " + "x" * 20, self.LIM)
        self.assertTrue(any("найкращ" in x for x in got))
        self.assertTrue(any("лучш" in x for x in got))
        self.assertTrue(any("100%" in x for x in got))


class RiskyWordTests(unittest.TestCase):
    LIM = {"title_min": 1, "title_max": 100, "desc_min": 1, "desc_max": 500}

    def test_word_start_only(self):
        self.assertEqual(check("Лежак", "Улучшенный материал", self.LIM), [])
        self.assertTrue(check("Лежак", "Лучший материал", self.LIM))


class RunTests(unittest.TestCase):
    def test_example_flags(self):
        out, info = run(ROWS, CFG)
        by = {r["sku"]: r["issues"] for r in out}
        self.assertEqual(by["A1"], "")
        self.assertIn("same title as row 2", by["A4"])  # A1 is row 2
        self.assertIn("missing: size", by["A5"])
        self.assertEqual(info, {"rows": 5, "with_issues": 2})

    def test_required_only_reported_when_listed(self):
        cfg = dict(CFG, required=[])
        out, _ = run([ROWS[4]], cfg)
        self.assertNotIn("missing", out[0]["issues"])


class CliTests(unittest.TestCase):
    def test_cli_and_formula_guard(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "p.csv")
            with open(p, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["sku", "type", "type_ru", "brand", "model", "size"])
                w.writerow(["=1+1", "Лежак", "Лежанка", "Z", "C", "40x30"])
            out = os.path.join(d, "o.csv")
            self.assertEqual(main([p, "--config", os.path.join(ROOT, "examples", "config.json"), "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                self.assertEqual(list(csv.DictReader(f))[0]["sku"], "'=1+1")


if __name__ == "__main__":
    unittest.main()
