import io
import zipfile
from django.test import SimpleTestCase

from datasets.utils import pair_transcriptions_from_zip


def _make_zip(entries: dict[str, bytes]) -> io.BytesIO:
    """Build an in-memory zip. entries = {archive_name: content bytes}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    buf.seek(0)
    return buf


class PairTranscriptionsFromZipTests(SimpleTestCase):
    # SimpleTestCase: no database access required.

    def test_paire_simple(self):
        z = _make_zip({"l1.png": b"img", "l1.txt": "bonjour".encode("utf-8")})
        r = pair_transcriptions_from_zip(z)
        self.assertEqual(r["pairs"], {"l1": "bonjour"})
        self.assertEqual(r["report"], "")
        self.assertEqual(r["n_images_ignored"], 0)
        self.assertEqual(r["n_txt_ignored"], 0)
        self.assertEqual(r["n_other_files"], 0)

    def test_sous_dossiers(self):
        z = _make_zip({
            "ms_A/l1.png": b"img", "ms_A/l1.txt": "a".encode(),
            "ms_B/l1.png": b"img", "ms_B/l1.txt": "b".encode(),
        })
        r = pair_transcriptions_from_zip(z)
        # meme radical l1 dans deux dossiers -> deux paires distinctes
        self.assertEqual(r["pairs"], {"ms_A/l1": "a", "ms_B/l1": "b"})
        self.assertEqual(r["report"], "")

    def test_image_sans_txt(self):
        z = _make_zip({"l1.png": b"img", "l2.png": b"img", "l1.txt": "a".encode()})
        r = pair_transcriptions_from_zip(z)
        self.assertEqual(r["pairs"], {"l1": "a"})
        self.assertEqual(r["n_images_ignored"], 1)
        self.assertIn("l2.png", r["dropped"]["img_no_txt"])

    def test_txt_sans_image(self):
        z = _make_zip({"l1.png": b"img", "l1.txt": "a".encode(), "l2.txt": "orphan".encode()})
        r = pair_transcriptions_from_zip(z)
        self.assertEqual(r["pairs"], {"l1": "a"})
        self.assertEqual(r["n_txt_ignored"], 1)
        self.assertIn("l2.txt", r["dropped"]["txt_no_img"])

    def test_radical_image_ambigu(self):
        # deux images de meme radical dans le meme dossier + un txt : pas de paire
        z = _make_zip({"l1.png": b"a", "l1.jpg": b"b", "l1.txt": "x".encode()})
        r = pair_transcriptions_from_zip(z)
        self.assertEqual(r["pairs"], {})
        self.assertEqual(r["n_images_ignored"], 2)  # les DEUX fichiers image
        self.assertEqual(sorted(r["dropped"]["ambiguous_img"]), ["l1.jpg", "l1.png"])

    def test_radical_txt_ambigu(self):
        # l1.txt ET l1.TXT : on ne tranche pas, on signale
        z = _make_zip({"l1.png": b"img", "l1.txt": "a".encode(), "l1.TXT": "b".encode()})
        r = pair_transcriptions_from_zip(z)
        self.assertEqual(r["pairs"], {})
        self.assertEqual(r["n_txt_ignored"], 2)
        self.assertEqual(sorted(r["dropped"]["ambiguous_txt"]), ["l1.TXT", "l1.txt"])

    def test_fichiers_parasites(self):
        z = _make_zip({
            "l1.png": b"img", "l1.txt": "a".encode(),
            "meta.xml": b"<xml/>", "notice.pdf": b"%PDF",
        })
        r = pair_transcriptions_from_zip(z)
        self.assertEqual(r["pairs"], {"l1": "a"})
        self.assertEqual(r["n_other_files"], 2)
        self.assertIn("unrecognized", r["report"])

    def test_ignore_caches_et_macosx(self):
        z = _make_zip({
            "l1.png": b"img", "l1.txt": "a".encode(),
            ".DS_Store": b"junk", "__MACOSX/l1.png": b"junk", "dir/.hidden.txt": b"x",
        })
        r = pair_transcriptions_from_zip(z)
        self.assertEqual(r["pairs"], {"l1": "a"})
        # caches et __MACOSX totalement ignores : ils ne comptent nulle part
        self.assertEqual(r["n_other_files"], 0)
        self.assertEqual(r["report"], "")

    def test_zip_mal_forme_que_des_xml(self):
        # cas Zenodo brut : aucune paire, mais on veut que ce soit VISIBLE
        z = _make_zip({"a.xml": b"<x/>", "b.xml": b"<x/>"})
        r = pair_transcriptions_from_zip(z)
        self.assertEqual(r["pairs"], {})
        self.assertEqual(r["n_other_files"], 2)
        self.assertNotEqual(r["report"], "")  # le probleme ne passe pas inapercu
    def test_archive_corrompue(self):
        # buffer qui n'est pas un zip valide : on ne doit PAS crasher
        bad = io.BytesIO(b"this is not a zip file at all")
        r = pair_transcriptions_from_zip(bad)
        self.assertEqual(r["pairs"], {})
        self.assertNotEqual(r["report"], "")     # le probleme reste visible
        self.assertIn("archive", r["report"])