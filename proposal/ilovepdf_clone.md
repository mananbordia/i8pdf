# PaperForge - Implementation Plan

A fast, free, locally-run PDF toolkit. Originally inspired by iLovePDF but with its own identity, design, and architecture.

## Current State (Implemented)

### Backend (`pdf_tool.py`)
All core functions implemented with CLI subcommands:
- **images_to_pdf** — Convert images to PDF with optional A4 fitting and shuffle
- **merge_pdfs** — Combine multiple PDFs into one
- **split_pdf** — Extract each page into a separate PDF
- **protect_pdf** — Encrypt a PDF with a password
- **unlock_pdf** — Remove password protection (requires correct password)
- **rotate_pdf** — Rotate all pages by 90/180/270 degrees

### API (`app.py`)
Flask server with REST endpoints for all features:
- `POST /api/img2pdf` — images to PDF (supports `fit_a4` toggle)
- `POST /api/merge` — merge PDFs
- `POST /api/split` — split PDF (returns zip)
- `POST /api/protect` — password-protect PDF
- `POST /api/unlock` — unlock encrypted PDF
- `POST /api/rotate` — rotate PDF pages

### Frontend
- **Landing page** (`index.html`) — Tool card grid with unique branding
- **Tool page** (`tool.html`) — Single data-driven Jinja template for all tools
- **JS** (`static/js/app.js`) — Handles dropzone, file list, drag reorder, toggles, fields, processing, PDF preview, download
- **CSS** (`static/css/style.css`) — Dark theme design system with per-tool accent colors

### Tests
- `test_pdf_tool.py` — Unit tests for all backend functions including edge cases
- `test_app.py` — Integration tests for all API endpoints

## Remaining Features (Not Yet Implemented)

| Feature | Complexity | Notes |
|---|---|---|
| Compress PDF | Medium | Needs Ghostscript or image quality reduction approach. `pypdf` alone cannot compress. |
| PDF to JPG | Medium | Requires `pdf2image` + system `poppler` dependency. |
| Add Watermark | Medium | Text overlay via `pypdf` or image overlay via `reportlab`. |
| Organize PDF | High | Needs page-thumbnail rendering (pdf.js) + drag-reorder UI for individual pages within a PDF. |

## Differentiation from iLovePDF

- **Name & branding**: PaperForge with indigo/purple palette, not iLovePDF's red/heart
- **Runs locally**: No cloud uploads, no sign-ups, no file size limits beyond server memory
- **Data-driven architecture**: Single `tool.html` template + `app.js` handles all tools via config — adding a new tool is just a dict entry in `app.py`
- **PDF preview**: Inline preview before download (not auto-download)
- **Dark-first design**: Built for dark mode with per-tool accent colors

## Future Differentiation Ideas

- **Pipeline/chaining**: Let users chain operations (e.g., images -> PDF -> compress -> protect) in a single flow
- **Command palette**: Search-based tool discovery ("merge", "lock", "compress")
- **Live page thumbnails**: Render actual PDF pages using pdf.js for merge/split/organize tools
- **Drag between tools**: Output of one tool feeds into the next
