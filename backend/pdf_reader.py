import pymupdf  # PyMuPDF


class PdfError(Exception):
    """Raised when an uploaded file cannot be turned into text. Safe to show to the user."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def extract_text_from_pdf_bytes(data, max_pages=30):
    """Extract text from PDF bytes (nothing is written to disk).

    Returns (text, total_pages, pages_read).
    """
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception:
        raise PdfError("This file could not be read as a PDF.")

    try:
        if document.needs_pass:
            raise PdfError("This PDF is password protected. Please upload an unlocked copy.")

        total_pages = document.page_count
        if total_pages == 0:
            raise PdfError("This PDF has no pages.")

        pages_read = min(total_pages, max_pages)
        parts = []
        for index in range(pages_read):
            parts.append(document[index].get_text())

        return "".join(parts), total_pages, pages_read
    except PdfError:
        raise
    except Exception:
        raise PdfError("This PDF could not be processed. It may be damaged.")
    finally:
        document.close()
