#!/usr/bin/env python3
"""
intake.py: inventory a folder of faculty content and extract its text so the
agents read the material once, in plain text, with page and slide markers.

    python3 intake.py <faculty-folder> --out <work>/intake

Writes
  <out>/inventory.json      one row per file: path, kind, size, pages or
                            slides, word count, extracted text file, notes
  <out>/text/<name>.txt     extracted text, with [page N] / [slide N] markers
                            and slide speaker notes under [notes]

  <out>/pages/<name>-pNN.png  page pictures saved for the content-inventory
                            agent to read itself, when OCR is missing or unsure

Handles .docx, .pptx, .pdf, .md, .txt, .html, .csv, .vtt and .srt. Scanned PDF
pages (pages with almost no text layer) and photos or scans of handouts
(.png, .jpg, .tif and similar) are read with OCR through ocr.py. Every OCR'd
page is marked in the text with [page N, OCR] and listed in the inventory with
its confidence. Pages that could not be read, or read with low confidence, are
saved as pictures and listed under needs_visual_read. Lists video and audio
files with sizes (it does not open them) and flags anything it cannot read.
python-docx, python-pptx and pypdf are used when installed; without them those
file types are listed as "not extracted".
"""

import argparse
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ocr  # noqa: E402

MEDIA = {".mp4", ".mov", ".m4v", ".webm", ".mp3", ".wav", ".m4a", ".avi", ".mkv"}
IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".tif", ".tiff"}
TEXT = {".md", ".txt", ".csv"}
CAPTION = {".vtt", ".srt"}
OCR_IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".gif"}
MIN_PAGE_WORDS = 25   # a PDF page with fewer extracted words is treated as scanned
PAGES_DIR = None      # set in main()


def read_docx(p):
    import docx  # python-docx
    d = docx.Document(str(p))
    lines = []
    for para in d.paragraphs:
        t = para.text.strip()
        if not t:
            continue
        style = (para.style.name or "").lower() if para.style is not None else ""
        if style.startswith("heading"):
            lvl = re.sub(r"\D", "", style) or "1"
            lines.append("%s %s" % ("#" * int(lvl), t))
        elif "list" in style:
            lines.append("- " + t)
        else:
            lines.append(t)
    for ti, table in enumerate(d.tables, start=1):
        lines.append("[table %d]" % ti)
        for row in table.rows:
            lines.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n".join(lines), {"paragraphs": len(d.paragraphs), "tables": len(d.tables)}


def read_pptx(p):
    from pptx import Presentation
    pres = Presentation(str(p))
    out, images = [], 0
    for i, slide in enumerate(pres.slides, start=1):
        out.append("[slide %d]" % i)
        for shape in slide.shapes:
            if shape.shape_type == 13:
                images += 1
                out.append("[image on slide %d: %s]" % (i, shape.name))
            if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    t = "".join(r.text for r in para.runs).strip()
                    if t:
                        out.append(("  " * para.level) + t)
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                out.append("[notes] " + notes)
    return "\n".join(out), {"slides": len(pres.slides), "images": images}


def safe_name(rel):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", rel)


def read_pdf(p, rel):
    from pypdf import PdfReader
    r = PdfReader(str(p))
    layer = [(page.extract_text() or "").strip() for page in r.pages]
    scanned = [i + 1 for i, t in enumerate(layer) if len(t.split()) < MIN_PAGE_WORDS]
    info = {"pages": len(r.pages)}
    ocr_text, ocr_rows, visual = {}, [], []
    if scanned:
        name, _ = ocr.engine()
        info["scanned_pages"] = scanned
        info["ocr_engine"] = name or "none installed"
        try:
            for n, img in ocr.render_pdf_pages(p, scanned):
                res = ocr.ocr_image(img)
                good = res["text"] and len(res["text"].split()) >= 3
                if good:
                    ocr_text[n] = res["text"]
                    ocr_rows.append({"page": n, "confidence": res["confidence"], "words": len(res["text"].split())})
                if not good or (res["confidence"] or 0) < ocr.LOW_CONFIDENCE:
                    PAGES_DIR.mkdir(parents=True, exist_ok=True)
                    png = PAGES_DIR / ("%s-p%02d.png" % (safe_name(rel), n))
                    img.convert("L").save(png)
                    visual.append({"page": n, "image": "pages/" + png.name,
                                   "why": "low OCR confidence" if good else ("no OCR engine" if not name else "no text found by OCR")})
        except Exception as exc:  # renderer missing or page broken: flag, keep going
            info["note"] = "scanned pages not rendered: %s" % exc
            visual = [{"page": n, "image": None, "why": "could not render page"} for n in scanned]
    out = []
    for i, t in enumerate(layer, start=1):
        if i in ocr_text:
            out.append("[page %d, OCR]" % i)
            out.append(ocr_text[i])
        elif i in scanned:
            out.append("[page %d, scanned, not read: see needs_visual_read]" % i)
            if t:
                out.append(t)
        else:
            out.append("[page %d]" % i)
            out.append(t)
    if ocr_rows:
        info["ocr_pages"] = ocr_rows
    if visual:
        info["needs_visual_read"] = visual
    return "\n".join(out), info


def read_image(p, rel):
    """OCR a photo or scan of a handout. Images with no text are just listed."""
    info = {"note": "needs alt text or a long description if it is used"}
    name, _ = ocr.engine()
    parts, rows, visual = [], [], []
    for n, img in ocr.open_image_frames(p):
        if min(img.size) < 64:  # icons and placeholders
            continue
        res = ocr.ocr_image(img)
        words = len(res["text"].split()) if res["text"] else 0
        if words >= 5:
            parts.append("[image page %d, OCR]" % n)
            parts.append(res["text"])
            rows.append({"page": n, "confidence": res["confidence"], "words": words})
            if (res["confidence"] or 0) < ocr.LOW_CONFIDENCE:
                visual.append({"page": n, "image": None, "why": "low OCR confidence; read the original image"})
        elif not name:
            visual.append({"page": n, "image": None, "why": "no OCR engine; read the original image if it holds text"})
    if name:
        info["ocr_engine"] = name
    if rows:
        info["ocr_pages"] = rows
        info["note"] = "picture of text (scan or photo); OCR text extracted. Check it against the image before quoting."
    if visual:
        info["needs_visual_read"] = visual
    return ("\n".join(parts) if parts else None), info


def read_html(p):
    s = p.read_text(encoding="utf-8", errors="replace")
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?i)<h([1-6])[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", s)
    s = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h[1-6]>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(re.sub(r"[ \t]+", " ", s)).strip(), {}


def read_caption(p):
    s = p.read_text(encoding="utf-8", errors="replace")
    lines = [l for l in s.splitlines() if l.strip() and "-->" not in l and not l.strip().isdigit() and l.strip() != "WEBVTT"]
    return "\n".join(lines), {"caption_file": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root = pathlib.Path(a.folder).resolve()
    if not root.is_dir():
        print("ERROR not a folder: %s" % root)
        sys.exit(1)
    out = pathlib.Path(a.out)
    global PAGES_DIR
    PAGES_DIR = out / "pages"
    (out / "text").mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name.startswith((".", "~$")):
            continue
        rel = p.relative_to(root).as_posix()
        ext = p.suffix.lower()
        row = {"path": rel, "ext": ext, "bytes": p.stat().st_size}
        text, info, kind = None, {}, "other"
        try:
            if ext == ".docx":
                kind = "document"; text, info = read_docx(p)
            elif ext == ".pptx":
                kind = "slides"; text, info = read_pptx(p)
            elif ext == ".pdf":
                kind = "pdf"; text, info = read_pdf(p, rel)
            elif ext in (".html", ".htm"):
                kind = "html"; text, info = read_html(p)
            elif ext in TEXT:
                kind = "text"; text = p.read_text(encoding="utf-8", errors="replace")
            elif ext in CAPTION:
                kind = "captions"; text, info = read_caption(p)
            elif ext in MEDIA:
                kind = "media"; info = {"note": "existing faculty media; check captions and whether it can be reused"}
            elif ext in OCR_IMAGE:
                kind = "image"; text, info = read_image(p, rel)
            elif ext in IMAGE:
                kind = "image"; info = {"note": "needs alt text or a long description if it is used"}
            else:
                info = {"note": "not a supported type; review by hand"}
        except ImportError as exc:
            info = {"note": "not extracted (missing library: %s)" % exc.name}
        except Exception as exc:  # unreadable file: flag, do not stop the run
            info = {"note": "could not read: %s" % exc}
        row["kind"] = kind
        row.update(info)
        if text is not None:
            name = safe_name(rel) + ".txt"
            (out / "text" / name).write_text(text, encoding="utf-8")
            row["text_file"] = "text/" + name
            row["words"] = len(text.split())
        rows.append(row)
    inv = {"source_folder": str(root), "files": rows,
           "totals": {"files": len(rows), "words": sum(r.get("words", 0) for r in rows),
                      "media": sum(1 for r in rows if r["kind"] == "media"),
                      "unreadable": sum(1 for r in rows if "could not read" in r.get("note", "") or "not extracted" in r.get("note", "")),
                      "ocr_pages": sum(len(r.get("ocr_pages", [])) for r in rows),
                      "needs_visual_read": sum(len(r.get("needs_visual_read", [])) for r in rows)},
           "ocr_engine": ocr.engine()[0] or "none installed (pip install rapidocr_onnxruntime pypdfium2)"}
    (out / "inventory.json").write_text(json.dumps(inv, indent=2), encoding="utf-8")
    for r in rows:
        bits = [r["kind"]] + ["%s %s" % (k, r[k]) for k in ("slides", "pages", "words") if k in r]
        if r.get("ocr_pages"):
            bits.append("OCR %d page(s), lowest confidence %.2f" % (len(r["ocr_pages"]), min(x["confidence"] for x in r["ocr_pages"])))
        if r.get("needs_visual_read"):
            bits.append("%d page(s) need a visual read" % len(r["needs_visual_read"]))
        print("%-46s %s%s" % (r["path"], ", ".join(bits), ("  NOTE " + r["note"]) if "note" in r else ""))
    print("Inventory: %d files, %d words extracted, %d media files, %d page(s) OCR'd with %s, %d page(s) need a visual read -> %s" % (
        inv["totals"]["files"], inv["totals"]["words"], inv["totals"]["media"], inv["totals"]["ocr_pages"], inv["ocr_engine"],
        inv["totals"]["needs_visual_read"], out / "inventory.json"))


if __name__ == "__main__":
    main()
