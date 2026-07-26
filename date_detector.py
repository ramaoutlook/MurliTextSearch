"""
Detects the murli type from a file name, and finds date-heading paragraphs
inside a document according to the type-specific pattern.
"""
import re

# Avyakt Murli date heading, e.g.:
#   "21-01-69 ओम शान्ति अव्यक्त बापदादा मधुबन"
AVYAKT_DATE_RE = re.compile(
    r'^\s*\d{1,2}-\d{1,2}-\d{2,4}\s+ओम\s*शान्ति\s+अव्यक्त\s+बापदादा\s+मधुबन'
)

# Sakar Murli date heading, e.g.:
#   "१-१-९४ प्रात:मुरली ओम् शान्ति ''बापदादा '' मधुबन"
#   "३-१-९४ प्रात: मुरली ओम् शान्ति ''अव्यक्त-बापदादा '' रिवाइज़-२.८.७२ मधुबन"
# Devanagari-digit date, followed (allowing an optional space) by "प्रात:मुरली".
SAKAR_DATE_RE = re.compile(
    r'^\s*[०-९]{1,2}-[०-९]{1,2}-[०-९]{2,4}\s*प्रात\s*:?\s*मुरली'
)

MURLI_TYPE_SAKAR = "SakarMurli"
MURLI_TYPE_AVYAKT = "AvyaktMurli"


def detect_murli_type(file_path: str) -> str:
    """Determine murli type from the file name (case-insensitive substring match)."""
    lower_name = file_path.lower()
    has_sakar = "sakar murli" in lower_name or "sakar_murli" in lower_name
    has_avyakt = "avyakt murli" in lower_name or "avyakt_murli" in lower_name

    if has_sakar and not has_avyakt:
        return MURLI_TYPE_SAKAR
    if has_avyakt and not has_sakar:
        return MURLI_TYPE_AVYAKT
    if has_sakar and has_avyakt:
        # Ambiguous name — fall back to whichever keyword appears first in the name.
        idx_sakar = lower_name.find("sakar murli")
        idx_avyakt = lower_name.find("avyakt murli")
        return MURLI_TYPE_SAKAR if idx_sakar < idx_avyakt else MURLI_TYPE_AVYAKT

    raise ValueError(
        "Could not determine murli type from file name. "
        "The file name must contain either 'Sakar Murli' or 'Avyakt Murli'."
    )


def is_date_heading(paragraph_text: str, murli_type: str) -> bool:
    """Return True if this paragraph text is a date-heading line for the given type."""
    text = paragraph_text.strip()
    if not text:
        return False
    if murli_type == MURLI_TYPE_SAKAR:
        return bool(SAKAR_DATE_RE.match(text))
    if murli_type == MURLI_TYPE_AVYAKT:
        return bool(AVYAKT_DATE_RE.match(text))
    raise ValueError(f"Unknown murli type: {murli_type}")


def extract_date_string(paragraph_text: str, murli_type: str) -> str:
    """Extract just the date portion (e.g. '21-01-69' or '१-१-९४') from a heading line."""
    text = paragraph_text.strip()
    if murli_type == MURLI_TYPE_SAKAR:
        m = re.match(r'^\s*([०-९]{1,2}-[०-९]{1,2}-[०-९]{2,4})', text)
    else:
        m = re.match(r'^\s*(\d{1,2}-\d{1,2}-\d{2,4})', text)
    return m.group(1) if m else text
