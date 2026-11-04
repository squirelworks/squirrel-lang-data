"""Tests for tools/importers/freq_tags.py (no wordfreq needed)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "importers"))
import freq_tags  # noqa: E402


class FreqTags(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(freq_tags.variants("дешёвый", "ru"), ["дешёвый", "дешевый"])
        self.assertEqual(freq_tags.variants("मेज़", "hi"), ["मेज़", "मेज"])
        self.assertIn("महंगा", freq_tags.variants("महँगा", "hi"))
        self.assertEqual(freq_tags.variants("ёлка", "uk"), ["ёлка"])

    def test_tag_entries(self):
        header = {"schema": "vocab@1", "notes": ["Written for this project."]}
        entries = [{"word": "a", "freq": "rare"}, {"word": "b"}]
        head, out, n = freq_tags.tag_entries(header, entries, lambda w: "core")
        self.assertEqual(n, 1)
        self.assertEqual([e["freq"] for e in out], ["rare", "core"])
        self.assertEqual(head["notes"][-1], freq_tags.NOTE)
        again = freq_tags.tag_entries(head, out, lambda w: "common")
        self.assertEqual(again[2], 0)
        self.assertEqual(again[0]["notes"], head["notes"])


if __name__ == "__main__":
    unittest.main()
