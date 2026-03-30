#!/usr/bin/env python3
"""Flask web server for I8PDF."""

import os
import tempfile
import uuid
import zipfile

from flask import Flask, render_template, request, send_file

from pdf_tool import images_to_pdf, merge_pdfs, split_pdf, protect_pdf, unlock_pdf, rotate_pdf

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB upload limit

TOOLS = {
    "merge": {
        "title": "Merge PDF",
        "desc": "Combine multiple PDFs into a single document. Drag to reorder.",
        "icon": "fa-layer-group",
        "accent": "merge",
        "accept": ".pdf",
        "multiple": True,
        "endpoint": "/api/merge",
        "fields": [],
        "result_type": "pdf",
    },
    "split": {
        "title": "Split PDF",
        "desc": "Extract every page into its own file. Download as a zip.",
        "icon": "fa-scissors",
        "accent": "split",
        "accept": ".pdf",
        "multiple": False,
        "endpoint": "/api/split",
        "fields": [],
        "result_type": "download",
    },
    "protect": {
        "title": "Protect PDF",
        "desc": "Encrypt a PDF with a password.",
        "icon": "fa-lock",
        "accent": "protect",
        "accept": ".pdf",
        "multiple": False,
        "endpoint": "/api/protect",
        "fields": [{"name": "password", "type": "password", "label": "Password", "required": True}],
        "result_type": "download",
    },
    "unlock": {
        "title": "Unlock PDF",
        "desc": "Remove password protection from a PDF.",
        "icon": "fa-lock-open",
        "accent": "unlock",
        "accept": ".pdf",
        "multiple": False,
        "endpoint": "/api/unlock",
        "fields": [{"name": "password", "type": "password", "label": "Password", "required": True}],
        "result_type": "pdf",
    },
    "rotate": {
        "title": "Rotate PDF",
        "desc": "Rotate all pages of a PDF.",
        "icon": "fa-rotate-right",
        "accent": "rotate",
        "accept": ".pdf",
        "multiple": False,
        "endpoint": "/api/rotate",
        "fields": [{"name": "degrees", "type": "select", "label": "Rotation", "options": [
            {"value": "90", "text": "90\u00b0 clockwise"},
            {"value": "180", "text": "180\u00b0"},
            {"value": "270", "text": "270\u00b0 clockwise (90\u00b0 counter-clockwise)"},
        ]}],
        "result_type": "pdf",
    },
    "img2pdf": {
        "title": "Images to PDF",
        "desc": "Convert images into a PDF. Drag to reorder pages.",
        "icon": "fa-image",
        "accent": "img2pdf",
        "accept": "image/*",
        "multiple": True,
        "endpoint": "/api/img2pdf",
        "fields": [],
        "toggles": [{"name": "fit_a4", "label": "Fit to A4", "default": True}],
        "result_type": "pdf",
    },
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tool/<tool_name>")
def tool_page(tool_name):
    if tool_name not in TOOLS:
        return "Tool not found", 404
    return render_template("tool.html", tool_name=tool_name, tool=TOOLS[tool_name])


def _save_uploads(files, tmp_dir):
    """Save uploaded files to tmp_dir, return list of paths."""
    saved = []
    for f in files:
        if f.filename == "":
            continue
        safe_name = f"{uuid.uuid4().hex}_{f.filename}"
        path = os.path.join(tmp_dir, safe_name)
        f.save(path)
        saved.append(path)
    return saved


@app.route("/api/img2pdf", methods=["POST"])
def api_img2pdf():
    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return {"error": "No images uploaded."}, 400

    fit_a4 = request.form.get("fit_a4", "false").lower() == "true"

    tmp_dir = tempfile.mkdtemp()
    try:
        saved_paths = _save_uploads(files, tmp_dir)
        if not saved_paths:
            return {"error": "No valid images uploaded."}, 400

        output_path = os.path.join(tmp_dir, "output.pdf")
        images_to_pdf(saved_paths, output_path, fit_a4=fit_a4)

        return send_file(output_path, mimetype="application/pdf",
                         as_attachment=True, download_name="output.pdf")
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/merge", methods=["POST"])
def api_merge():
    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return {"error": "No PDFs uploaded."}, 400

    tmp_dir = tempfile.mkdtemp()
    try:
        saved_paths = _save_uploads(files, tmp_dir)
        if not saved_paths:
            return {"error": "No valid PDFs uploaded."}, 400

        output_path = os.path.join(tmp_dir, "merged.pdf")
        merge_pdfs(saved_paths, output_path)

        return send_file(output_path, mimetype="application/pdf",
                         as_attachment=True, download_name="merged.pdf")
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/split", methods=["POST"])
def api_split():
    file = request.files.get("files")
    if not file or file.filename == "":
        return {"error": "No PDF uploaded."}, 400

    tmp_dir = tempfile.mkdtemp()
    try:
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        path = os.path.join(tmp_dir, safe_name)
        file.save(path)

        out_dir = os.path.join(tmp_dir, "split_output")
        saved_paths = split_pdf(path, out_dir)

        zip_path = os.path.join(tmp_dir, "split_pages.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for p in saved_paths:
                zipf.write(p, os.path.basename(p))

        return send_file(zip_path, mimetype="application/zip",
                         as_attachment=True, download_name="split_pages.zip")
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/protect", methods=["POST"])
def api_protect():
    file = request.files.get("files")
    if not file or file.filename == "":
        return {"error": "No PDF uploaded."}, 400

    password = request.form.get("password")
    if not password:
        return {"error": "Password is required."}, 400

    tmp_dir = tempfile.mkdtemp()
    try:
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        path = os.path.join(tmp_dir, safe_name)
        file.save(path)

        output_path = os.path.join(tmp_dir, "protected.pdf")
        protect_pdf(path, output_path, password)

        return send_file(output_path, mimetype="application/pdf",
                         as_attachment=True, download_name="protected.pdf")
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/unlock", methods=["POST"])
def api_unlock():
    file = request.files.get("files")
    if not file or file.filename == "":
        return {"error": "No PDF uploaded."}, 400

    password = request.form.get("password")
    if not password:
        return {"error": "Password is required."}, 400

    tmp_dir = tempfile.mkdtemp()
    try:
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        path = os.path.join(tmp_dir, safe_name)
        file.save(path)

        output_path = os.path.join(tmp_dir, "unlocked.pdf")
        unlock_pdf(path, output_path, password)

        return send_file(output_path, mimetype="application/pdf",
                         as_attachment=True, download_name="unlocked.pdf")
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/rotate", methods=["POST"])
def api_rotate():
    file = request.files.get("files")
    if not file or file.filename == "":
        return {"error": "No PDF uploaded."}, 400

    degrees = int(request.form.get("degrees", "90"))

    tmp_dir = tempfile.mkdtemp()
    try:
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        path = os.path.join(tmp_dir, safe_name)
        file.save(path)

        output_path = os.path.join(tmp_dir, "rotated.pdf")
        rotate_pdf(path, output_path, degrees=degrees)

        return send_file(output_path, mimetype="application/pdf",
                         as_attachment=True, download_name="rotated.pdf")
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True, port=5050)
