"""
OCR Service
-----------
Converts an uploaded PDF/image lab report to extracted text
using Tesseract OCR + OpenCV preprocessing.
"""

import io
import os
import tempfile
import logging
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Optional: set tesseract path on Windows
_TESS_CMD = os.environ.get("TESSERACT_CMD")
if _TESS_CMD:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = _TESS_CMD


def _preprocess(img: Image.Image) -> "np.ndarray":
    """Convert PIL image → greyscale → adaptive threshold → deskewed."""
    import cv2

    arr = np.array(img.convert("RGB"))
    grey = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Adaptive threshold to handle uneven illumination (scanned docs)
    thresh = cv2.adaptiveThreshold(
        grey, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

    # Mild denoise
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)

    return denoised


def _ocr_image(img: Image.Image) -> str:
    """Run Tesseract on a preprocessed PIL image."""
    import pytesseract

    processed = _preprocess(img)
    pil_proc  = Image.fromarray(processed)

    config = "--oem 3 --psm 6 -c preserve_interword_spaces=1"
    text   = pytesseract.image_to_string(pil_proc, config=config, lang="eng")
    return text


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Main entry point.
    Accepts PDF or image bytes, returns full extracted text string.
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _extract_from_pdf(file_bytes)
    elif suffix in {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}:
        return _extract_from_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _extract_from_pdf(file_bytes: bytes) -> str:
    """Convert PDF pages to images then OCR each page."""
    try:
        from pdf2image import convert_from_bytes
    except ImportError:
        raise RuntimeError("pdf2image not installed. Run: pip install pdf2image")

    pages = convert_from_bytes(file_bytes, dpi=250, fmt="jpeg")
    logger.info(f"PDF has {len(pages)} page(s)")

    all_text = []
    for i, page in enumerate(pages):
        logger.info(f"OCR page {i+1}/{len(pages)}")
        text = _ocr_image(page)
        all_text.append(text)

    return "\n\n".join(all_text)


def _extract_from_image(file_bytes: bytes) -> str:
    """OCR a single image file."""
    img  = Image.open(io.BytesIO(file_bytes))
    text = _ocr_image(img)
    return text
