import os
import tempfile
import unittest
from PIL import Image

from pypdf import PdfReader
from pdf_tool import images_to_pdf, merge_pdfs, split_pdf, protect_pdf, unlock_pdf, rotate_pdf

class TestPdfTool(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_image(self, name="img.png", size=(100, 100)):
        path = os.path.join(self.tmp, name)
        Image.new("RGB", size, color="red").save(path)
        return path

    def _make_pdf(self, name="test.pdf", pages=1):
        img_paths = [self._make_image(f"img_{i}.png") for i in range(pages)]
        out = os.path.join(self.tmp, name)
        images_to_pdf(img_paths, out)
        return out

    # --- images_to_pdf ---
    def test_images_to_pdf(self):
        img = self._make_image()
        output = os.path.join(self.tmp, "output.pdf")
        images_to_pdf([img], output)
        self.assertTrue(os.path.exists(output))

    def test_images_to_pdf_fit_a4(self):
        small = self._make_image("small.png", size=(50, 50))
        wide = self._make_image("wide.png", size=(800, 200))
        output = os.path.join(self.tmp, "a4.pdf")
        images_to_pdf([small, wide], output, fit_a4=True)
        self.assertTrue(os.path.exists(output))

    def test_images_to_pdf_empty(self):
        with self.assertRaises(ValueError):
            images_to_pdf([], os.path.join(self.tmp, "empty.pdf"))

    def test_images_to_pdf_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            images_to_pdf(["/nonexistent.png"], os.path.join(self.tmp, "out.pdf"))

    # --- merge ---
    def test_merge_pdfs(self):
        pdf1 = self._make_pdf("1.pdf")
        pdf2 = self._make_pdf("2.pdf")
        merged = os.path.join(self.tmp, "merged.pdf")
        merge_pdfs([pdf1, pdf2], merged)
        self.assertTrue(os.path.exists(merged))
        self.assertEqual(len(PdfReader(merged).pages), 2)

    # --- split ---
    def test_split_pdf(self):
        pdf = self._make_pdf("multi.pdf", pages=3)
        out_dir = os.path.join(self.tmp, "split")
        result = split_pdf(pdf, out_dir)
        self.assertEqual(len(result), 3)
        for p in result:
            self.assertTrue(os.path.exists(p))

    # --- protect ---
    def test_protect_pdf(self):
        pdf = self._make_pdf("plain.pdf")
        protected = os.path.join(self.tmp, "protected.pdf")
        protect_pdf(pdf, protected, "secret")
        self.assertTrue(os.path.exists(protected))
        self.assertTrue(PdfReader(protected).is_encrypted)

    # --- unlock ---
    def test_unlock_pdf(self):
        pdf = self._make_pdf("plain.pdf")
        protected = os.path.join(self.tmp, "locked.pdf")
        protect_pdf(pdf, protected, "pass123")

        unlocked = os.path.join(self.tmp, "unlocked.pdf")
        unlock_pdf(protected, unlocked, "pass123")
        self.assertTrue(os.path.exists(unlocked))
        self.assertFalse(PdfReader(unlocked).is_encrypted)

    def test_unlock_wrong_password(self):
        pdf = self._make_pdf("plain.pdf")
        protected = os.path.join(self.tmp, "locked.pdf")
        protect_pdf(pdf, protected, "right")

        with self.assertRaises(ValueError):
            unlock_pdf(protected, os.path.join(self.tmp, "fail.pdf"), "wrong")

    def test_unlock_not_encrypted(self):
        pdf = self._make_pdf("plain.pdf")
        with self.assertRaises(ValueError):
            unlock_pdf(pdf, os.path.join(self.tmp, "fail.pdf"), "any")

    # --- rotate ---
    def test_rotate_pdf_90(self):
        pdf = self._make_pdf("orig.pdf")
        rotated = os.path.join(self.tmp, "rotated.pdf")
        rotate_pdf(pdf, rotated, degrees=90)
        self.assertTrue(os.path.exists(rotated))

    def test_rotate_pdf_180(self):
        pdf = self._make_pdf("orig.pdf")
        rotated = os.path.join(self.tmp, "rotated180.pdf")
        rotate_pdf(pdf, rotated, degrees=180)
        self.assertTrue(os.path.exists(rotated))

    def test_rotate_pdf_invalid_degrees(self):
        pdf = self._make_pdf("orig.pdf")
        with self.assertRaises(ValueError):
            rotate_pdf(pdf, os.path.join(self.tmp, "fail.pdf"), degrees=45)


if __name__ == "__main__":
    unittest.main()
