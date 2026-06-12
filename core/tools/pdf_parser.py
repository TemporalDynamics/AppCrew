import io
import httpx
from pypdf import PdfReader

from core.logger import get_logger

logger = get_logger("core.tools.pdf_parser")


async def download_and_extract_pdf(url: str) -> str:
    """Download a PDF from a URL and extract its text."""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            
            pdf_file = io.BytesIO(resp.content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text.strip()
    except Exception as e:
        logger.error("[PDF_PARSER] Failed to extract %s: %s", url, e)
        return ""
