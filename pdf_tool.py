#!/usr/bin/env python3
"""PDF Tool — Create and manipulate PDFs."""

import argparse
import random
import sys
from pathlib import Path
from typing import List

from PIL import Image
from pypdf import PdfReader, PdfWriter


A4_WIDTH_PT = 595
A4_HEIGHT_PT = 842
A4_DPI = 72


def _fit_image_to_a4(img: Image.Image) -> Image.Image:
    """Place an image centered on a white A4 page, scaled to fit."""
    render_dpi = 150
    page_w = int(A4_WIDTH_PT * render_dpi / A4_DPI)
    page_h = int(A4_HEIGHT_PT * render_dpi / A4_DPI)

    margin = 0.05
    max_w = int(page_w * (1 - 2 * margin))
    max_h = int(page_h * (1 - 2 * margin))

    img_w, img_h = img.size
    scale = min(max_w / img_w, max_h / img_h)

    resized = img.resize((int(img_w * scale), int(img_h * scale)), Image.LANCZOS)

    page = Image.new("RGB", (page_w, page_h), (255, 255, 255))
    x = (page_w - resized.width) // 2
    y = (page_h - resized.height) // 2
    page.paste(resized, (x, y))
    resized.close()
    return page


def images_to_pdf(
    image_paths: List[str], output: str, shuffle: bool = False, fit_a4: bool = False
) -> str:
    if not image_paths:
        raise ValueError("No image paths provided.")

    resolved = []
    for p in image_paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {p}")
        resolved.append(path)

    if shuffle:
        random.shuffle(resolved)

    pages = []
    for img_path in resolved:
        img = Image.open(img_path)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        if fit_a4:
            page = _fit_image_to_a4(img)
            img.close()
            pages.append(page)
        else:
            pages.append(img)

    first, *rest = pages
    first.save(output, "PDF", save_all=True, append_images=rest, resolution=100.0)

    for img in pages:
        img.close()

    return output


def merge_pdfs(pdf_paths: List[str], output: str) -> str:
    if not pdf_paths:
        raise ValueError("No PDF paths provided.")
        
    writer = PdfWriter()
    for path in pdf_paths:
        if not Path(path).exists():
            raise FileNotFoundError(f"PDF not found: {path}")
            
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
            
    with open(output, "wb") as fp:
        writer.write(fp)
    return output


def split_pdf(pdf_path: str, output_dir: str) -> List[str]:
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
    reader = PdfReader(pdf_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    base_name = Path(pdf_path).stem
    saved_paths = []
    
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        
        out_path = out_dir / f"{base_name}_page_{i+1}.pdf"
        with open(out_path, "wb") as fp:
            writer.write(fp)
        saved_paths.append(str(out_path))
        
    return saved_paths


def protect_pdf(pdf_path: str, output: str, password: str) -> str:
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    with open(output, "wb") as fp:
        writer.write(fp)
    return output


def unlock_pdf(pdf_path: str, output: str, password: str) -> str:
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    if not reader.is_encrypted:
        raise ValueError("PDF is not encrypted.")

    if not reader.decrypt(password):
        raise ValueError("Incorrect password.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    with open(output, "wb") as fp:
        writer.write(fp)
    return output


def rotate_pdf(pdf_path: str, output: str, degrees: int = 90) -> str:
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if degrees not in (90, 180, 270):
        raise ValueError("Degrees must be 90, 180, or 270.")

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)

    with open(output, "wb") as fp:
        writer.write(fp)
    return output


def main():
    parser = argparse.ArgumentParser(
        description="PDF Tool — Manipulate PDFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    img2pdf_parser = subparsers.add_parser("img2pdf", help="Convert images to a PDF.")
    img2pdf_parser.add_argument("images", nargs="+", help="Paths to image files.")
    img2pdf_parser.add_argument("-o", "--output", default="output.pdf", help="Output PDF path.")
    img2pdf_parser.add_argument("--shuffle", action="store_true", help="Randomly shuffle page order.")
    img2pdf_parser.add_argument("--fit-a4", action="store_true", help="Fit each image onto a uniform A4 page.")

    merge_parser = subparsers.add_parser("merge", help="Merge multiple PDFs into one.")
    merge_parser.add_argument("pdfs", nargs="+", help="Paths to PDF files.")
    merge_parser.add_argument("-o", "--output", default="merged.pdf", help="Output PDF path.")

    split_parser = subparsers.add_parser("split", help="Split a PDF into multiple one-page PDFs.")
    split_parser.add_argument("pdf", help="Path to PDF file.")
    split_parser.add_argument("-d", "--dir", default=".", help="Output directory path.")

    protect_parser = subparsers.add_parser("protect", help="Encrypt a PDF with a password.")
    protect_parser.add_argument("pdf", help="Path to PDF file.")
    protect_parser.add_argument("password", help="Password to encrypt with.")
    protect_parser.add_argument("-o", "--output", default="protected.pdf", help="Output PDF path.")

    unlock_parser = subparsers.add_parser("unlock", help="Remove password from an encrypted PDF.")
    unlock_parser.add_argument("pdf", help="Path to PDF file.")
    unlock_parser.add_argument("password", help="Password to decrypt with.")
    unlock_parser.add_argument("-o", "--output", default="unlocked.pdf", help="Output PDF path.")

    rotate_parser = subparsers.add_parser("rotate", help="Rotate all pages of a PDF.")
    rotate_parser.add_argument("pdf", help="Path to PDF file.")
    rotate_parser.add_argument("-d", "--degrees", type=int, default=90, choices=[90, 180, 270], help="Rotation degrees.")
    rotate_parser.add_argument("-o", "--output", default="rotated.pdf", help="Output PDF path.")

    args = parser.parse_args()

    try:
        if args.command == "img2pdf":
            result = images_to_pdf(args.images, args.output, shuffle=args.shuffle, fit_a4=args.fit_a4)
            print(f"PDF created: {result} ({len(args.images)} images)")
        elif args.command == "merge":
            result = merge_pdfs(args.pdfs, args.output)
            print(f"Merged PDF created: {result}")
        elif args.command == "split":
            result = split_pdf(args.pdf, args.dir)
            print(f"Split completed. Created {len(result)} files in {args.dir}")
        elif args.command == "protect":
            result = protect_pdf(args.pdf, args.output, args.password)
            print(f"Protected PDF created: {result}")
        elif args.command == "unlock":
            result = unlock_pdf(args.pdf, args.output, args.password)
            print(f"Unlocked PDF created: {result}")
        elif args.command == "rotate":
            result = rotate_pdf(args.pdf, args.output, degrees=args.degrees)
            print(f"Rotated PDF created: {result}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
