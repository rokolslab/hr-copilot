from __future__ import annotations

from io import BytesIO

import pdfplumber

from config import get_logger


logger = get_logger(__name__)


def clean_text(raw_text: str, max_chars: int | None = None) -> str:
    logger.debug(
        "Cleaning resume text",
        extra={
            "input_length": len(raw_text or ""),
            "max_chars": max_chars,
        },
    )

    lines = []
    for raw_line in (raw_text or "").splitlines():
        normalized_line = " ".join(raw_line.split())
        if normalized_line:
            lines.append(normalized_line)

    cleaned_text = "\n".join(lines).strip()
    if max_chars is not None and max_chars > 0:
        cleaned_text = cleaned_text[:max_chars].strip()

    logger.debug(
        "Resume text cleaned",
        extra={
            "output_length": len(cleaned_text),
            "line_count": len(lines),
        },
    )
    return cleaned_text


def extract_text_from_pdf(file_bytes: bytes) -> str:
    logger.info("Starting PDF resume extraction")
    logger.debug("PDF bytes received", extra={"byte_count": len(file_bytes or b"")})

    if not file_bytes:
        logger.warning("PDF extraction skipped because no file bytes were provided")
        return ""

    try:
        extracted_pages: list[str] = []
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            logger.debug("PDF opened successfully", extra={"page_count": len(pdf.pages)})
            for page_index, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                logger.debug(
                    "Extracted text from PDF page",
                    extra={
                        "page_index": page_index,
                        "page_text_length": len(page_text),
                    },
                )
                if page_text.strip():
                    extracted_pages.append(page_text)
    except Exception as error:  # pragma: no cover - exercised via callers
        logger.error(
            "PDF extraction failed",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )
        return ""

    extracted_text = "\n".join(extracted_pages).strip()
    if not extracted_text:
        logger.warning("PDF extraction completed but produced no text")
    else:
        logger.info(
            "PDF extraction completed successfully",
            extra={"text_length": len(extracted_text)},
        )

    return extracted_text


def prepare_resume_text(
    pdf_bytes: bytes | None,
    manual_text: str | None,
    max_chars: int,
) -> str:
    logger.info("Preparing resume text for analysis")
    logger.debug(
        "Resume input sources received",
        extra={
            "has_pdf_bytes": bool(pdf_bytes),
            "manual_text_length": len(manual_text or ""),
            "max_chars": max_chars,
        },
    )

    pdf_text = extract_text_from_pdf(pdf_bytes or b"") if pdf_bytes else ""
    if pdf_text:
        logger.debug("Using PDF text as primary resume source")
        return clean_text(pdf_text, max_chars=max_chars)

    cleaned_manual_text = clean_text(manual_text or "", max_chars=max_chars)
    if cleaned_manual_text:
        logger.warning("Falling back to manual resume text")
        return cleaned_manual_text

    logger.warning("No usable resume text was provided")
    return ""
