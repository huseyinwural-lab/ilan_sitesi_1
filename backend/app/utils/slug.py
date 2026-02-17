import re
import unicodedata

def slugify(text: str) -> str:
    """
    Normalizes string to URL-friendly slug.
    Example: "Lüks Daire Berlin!" -> "luks-daire-berlin"
    """
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii') # Strip accents for simple slug
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')
