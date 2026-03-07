import re
import pytesseract
from pdf2image import convert_from_bytes
import cv2
import numpy as np


class PDFParserError(Exception):
    pass


def extract_text_from_pdf(contents: bytes) -> str:
    pages = convert_from_bytes(contents)

    extracted_text = ""
    for page in pages:
        img_cv = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        text = pytesseract.image_to_string(thresh)
        extracted_text += text + "\n"

    return extracted_text


def clean_text(text: str) -> str:
    """
    Remove noise from extracted PDF text before sending to LLM:
    - blank lines
    - repeated lines (headers/footers that appear on every page)
    - page number lines
    """
    lines = text.splitlines()
    cleaned = []
    seen = set()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in seen:
            continue
        if re.match(r"^page\s+\d+", stripped, re.IGNORECASE):
            continue
        seen.add(stripped)
        cleaned.append(stripped)
    return "\n".join(cleaned)
