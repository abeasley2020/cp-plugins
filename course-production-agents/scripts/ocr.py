#!/usr/bin/env python3
"""
ocr.py: read text from scanned PDF pages and from photos or scans of handouts.

Used by intake.py. It picks the best engine that is installed:

  1. Tesseract, through pytesseract, when the tesseract program is on PATH.
  2. RapidOCR (pip install rapidocr_onnxruntime), which needs no system install
     and is the default on Windows and on locked-down machines.

PDF pages are rendered with pypdfium2 (pip install pypdfium2), or with the
poppler pdftoppm program when pypdfium2 is missing.

When no engine is installed, or a page reads with low confidence, intake saves
the page as a PNG and marks it "needs_visual_read" so the content-inventory
agent reads the picture itself and writes the transcription. Set CP_OCR to
tesseract, rapidocr or off to force a choice (off is for testing the fallback). Nothing is lost
either way; the inventory says which pages were read which way.

    python3 ocr.py <file.pdf|image> [...]     prints the text, for a quick test
"""

import os
import pathlib
import shutil
import statistics
import subprocess
import sys
import tempfile

RENDER_DPI = 220
LOW_CONFIDENCE = 0.80

_engine = None


def engine():
    """Return (name, callable) or (None, None). The callable takes a PIL image
    and returns (text, mean_confidence 0..1)."""
    global _engine
    if _engine is not None:
        return _engine
    _engine = (None, None)
    choice = os.environ.get("CP_OCR", "").lower()  # tesseract, rapidocr, or off
    if choice == "off":
        return _engine
    if shutil.which("tesseract") and choice in ("", "tesseract"):
        try:
            import pytesseract

            def run_tess(img):
                d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                lines, confs, key, cur = [], [], None, []
                for i, word in enumerate(d["text"]):
                    k = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
                    if k != key and cur:
                        lines.append(" ".join(cur)); cur = []
                    key = k
                    if word.strip():
                        cur.append(word.strip())
                        c = float(d["conf"][i])
                        if c >= 0:
                            confs.append(c / 100.0)
                if cur:
                    lines.append(" ".join(cur))
                return "\n".join(lines), (statistics.mean(confs) if confs else 0.0)

            _engine = ("tesseract", run_tess)
            return _engine
        except ImportError:
            pass
    if choice not in ("", "rapidocr"):
        return _engine
    try:
        from rapidocr_onnxruntime import RapidOCR
        import numpy as np
        rapid = RapidOCR()

        def run_rapid(img):
            res, _ = rapid(np.array(img.convert("RGB")))
            if not res:
                return "", 0.0
            # res rows: [box, text, score]; group boxes into lines by vertical centre
            items = []
            for box, text, score in res:
                ys = [pt[1] for pt in box]; xs = [pt[0] for pt in box]
                items.append(((min(ys) + max(ys)) / 2, min(xs), max(ys) - min(ys), text, float(score)))
            items.sort()
            lines, cur, cur_y, cur_h = [], [], None, None
            for y, x, h, text, score in items:
                if cur and abs(y - cur_y) > max(cur_h, h) * 0.6:
                    lines.append(cur); cur = []
                if not cur:
                    cur_y, cur_h = y, h
                cur.append((x, text))
            if cur:
                lines.append(cur)
            out = [" ".join(t for _, t in sorted(line)) for line in lines]
            return "\n".join(out), statistics.mean(i[4] for i in items)

        _engine = ("rapidocr", run_rapid)
    except ImportError:
        pass
    return _engine


def render_pdf_pages(path, page_numbers, dpi=RENDER_DPI):
    """Yield (page_number, PIL image) for the 1-based page numbers asked for."""
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(str(path))
        for n in page_numbers:
            yield n, pdf[n - 1].render(scale=dpi / 72.0).to_pil()
        pdf.close()
        return
    except ImportError:
        pass
    if not shutil.which("pdftoppm"):
        raise RuntimeError("no PDF renderer (pip install pypdfium2)")
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        for n in page_numbers:
            stem = pathlib.Path(td) / ("p%d" % n)
            subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(n), "-l", str(n), "-png", "-singlefile", str(path), str(stem)],
                           check=True, capture_output=True)
            img = Image.open(str(stem) + ".png"); img.load()
            yield n, img


def prepare(img):
    """Grayscale, and upscale small images, which helps both engines."""
    img = img.convert("L")
    if max(img.size) < 1400:
        f = 1400.0 / max(img.size)
        img = img.resize((int(img.width * f), int(img.height * f)))
    return img


def ocr_image(img):
    """Return dict: text, confidence, engine. text is '' when no engine."""
    name, fn = engine()
    if not fn:
        return {"text": "", "confidence": None, "engine": None}
    text, conf = fn(prepare(img))
    return {"text": text.strip(), "confidence": round(conf, 3), "engine": name}


def open_image_frames(path):
    """Yield (frame_number, PIL image) for an image file; multi-page TIFFs give several."""
    from PIL import Image, ImageSequence
    img = Image.open(str(path))
    for i, frame in enumerate(ImageSequence.Iterator(img), start=1):
        yield i, frame.copy()


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        pages = []
        if p.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            pages = render_pdf_pages(p, range(1, len(PdfReader(str(p)).pages) + 1))
        else:
            pages = open_image_frames(p)
        for n, img in pages:
            r = ocr_image(img)
            print("[%s page %d, %s, confidence %s]" % (p.name, n, r["engine"], r["confidence"]))
            print(r["text"])
