import unittest
from io import BytesIO
from PIL import Image
from pypdf import PdfWriter

from app import app


class TestApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _dummy_image(self):
        img = Image.new("RGB", (100, 100), color="red")
        buf = BytesIO()
        img.save(buf, "JPEG")
        buf.seek(0)
        return buf

    def _dummy_pdf(self, pages=1):
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=100, height=100)
        buf = BytesIO()
        writer.write(buf)
        buf.seek(0)
        return buf

    def _encrypted_pdf(self, password="test"):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.encrypt(password)
        buf = BytesIO()
        writer.write(buf)
        buf.seek(0)
        return buf

    # --- index ---
    def test_index(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        res.close()

    # --- tool pages ---
    def test_tool_page_valid(self):
        for tool in ["merge", "split", "protect", "unlock", "rotate", "img2pdf"]:
            res = self.client.get(f"/tool/{tool}")
            self.assertEqual(res.status_code, 200, f"Failed for /tool/{tool}")
            res.close()

    def test_tool_page_invalid(self):
        res = self.client.get("/tool/nonexistent")
        self.assertEqual(res.status_code, 404)
        res.close()

    # --- img2pdf ---
    def test_img2pdf(self):
        data = {"files": (self._dummy_image(), "test.jpg")}
        res = self.client.post("/api/img2pdf", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")
        res.close()

    def test_img2pdf_no_files(self):
        res = self.client.post("/api/img2pdf", data={}, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        res.close()

    # --- merge ---
    def test_merge(self):
        data = {"files": [
            (self._dummy_pdf(), "a.pdf"),
            (self._dummy_pdf(), "b.pdf"),
        ]}
        res = self.client.post("/api/merge", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")
        res.close()

    # --- split ---
    def test_split(self):
        data = {"files": (self._dummy_pdf(pages=2), "multi.pdf")}
        res = self.client.post("/api/split", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/zip")
        res.close()

    # --- protect ---
    def test_protect(self):
        data = {"files": (self._dummy_pdf(), "plain.pdf"), "password": "secret"}
        res = self.client.post("/api/protect", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        res.close()

    def test_protect_no_password(self):
        data = {"files": (self._dummy_pdf(), "plain.pdf")}
        res = self.client.post("/api/protect", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        res.close()

    # --- unlock ---
    def test_unlock(self):
        data = {"files": (self._encrypted_pdf("abc"), "locked.pdf"), "password": "abc"}
        res = self.client.post("/api/unlock", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")
        res.close()

    def test_unlock_wrong_password(self):
        data = {"files": (self._encrypted_pdf("right"), "locked.pdf"), "password": "wrong"}
        res = self.client.post("/api/unlock", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 500)
        res.close()

    # --- rotate ---
    def test_rotate(self):
        data = {"files": (self._dummy_pdf(), "test.pdf"), "degrees": "90"}
        res = self.client.post("/api/rotate", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")
        res.close()


if __name__ == "__main__":
    unittest.main()
