"""Tests for tools/gen_registry.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import gen_registry as gen  # noqa: E402


def write(path, data=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False), encoding="utf-8")


class Registry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.data, self.out = root / "data", root / "app" / "languages"
        write(self.data / "languages/japanese/meta.json", {
            "schema": "meta@1", "id": "japanese", "name": "Japanese", "nativeName": "日本語", "code": "jpn",
            "scripts": ["hiragana", "kanji"], "characterKeys": ["hiragana", "kanji"], "speech": "ja-JP",
            "varieties": ["classical-japanese", "okinawan"]})
        write(self.data / "languages/japanese/varieties/okinawan/meta.json", {
            "schema": "variety@1", "id": "okinawan", "parent": "japanese", "kind": "regional",
            "name": "Okinawan", "nativeName": "うちなーぐち", "code": "ryu"})
        write(self.data / "languages/japanese/varieties/classical-japanese/meta.json", {
            "schema": "variety@1", "id": "classical-japanese", "parent": "japanese", "kind": "historical",
            "name": "Classical Japanese", "code": "ojp", "period": {"label": "Heian to Edo", "from": 794, "to": 1868}})
        write(self.data / "languages/latin/meta.json", {
            "schema": "meta@1", "id": "latin", "name": "Latin", "nativeName": "Latina", "code": "lat",
            "scripts": ["latin"], "characterKeys": ["latin"]})
        for f in ("japanese/characters.js", "japanese/kanji.js", "japanese/vocab.js", "cjk/characters.js",
                  "latin/grammar.js", "latin/reference.json"):
            write(self.out / f)

    def tearDown(self):
        self.tmp.cleanup()

    def registry(self, files):
        text = files["registry.js"]
        self.assertTrue(text.startswith("// Generated from squirrel-lang-data "))
        return json.loads(text.split("window.LSD_LANGUAGE_REGISTRY =", 1)[1].strip().rstrip(";"))

    def test_desk_shape(self):
        reg = self.registry(gen.build(self.data, self.out))
        self.assertEqual(list(reg), ["japanese", "latin"])
        self.assertEqual(reg["japanese"]["writingSystems"], ["hiragana", "kanji"])
        self.assertNotIn("scripts", reg["japanese"])
        self.assertNotIn("varieties", reg["japanese"])
        self.assertEqual(reg["japanese"]["data"], {
            "characters": ["characters.js", "../cjk/characters.js", "kanji.js"], "vocab": "vocab.js"})
        self.assertEqual(reg["latin"]["data"], {"grammar": "grammar.js", "reference": "reference.json"})

    def test_meta_files_match_registry(self):
        files = gen.build(self.data, self.out)
        reg = self.registry(files)
        for id_ in reg:
            self.assertEqual(json.loads(files[f"{id_}/meta.json"]), reg[id_])

    def test_varieties_inherit(self):
        reg = self.registry(gen.build(self.data, self.out, with_varieties=True))
        oki = reg["okinawan"]
        self.assertEqual(oki["nativeName"], "うちなーぐち")
        self.assertEqual(oki["writingSystems"], ["hiragana", "kanji"])
        self.assertEqual(oki["speech"], "ja-JP")
        self.assertEqual((oki["parent"], oki["kind"], oki["code"]), ("japanese", "regional", "ryu"))
        self.assertEqual(reg["classical-japanese"]["nativeName"], "日本語")
        self.assertEqual(reg["classical-japanese"]["period"]["from"], 794)

    def test_check_mode(self):
        args = ["--out", str(self.out), "--data", str(self.data)]
        self.assertEqual(gen.main(args + ["--check"]), 1)
        self.assertEqual(gen.main(args), 0)
        self.assertEqual(gen.main(args + ["--check"]), 0)
        write(self.out / "latin/meta.json", "{}")
        self.assertEqual(gen.main(args + ["--check"]), 1)


if __name__ == "__main__":
    unittest.main()
