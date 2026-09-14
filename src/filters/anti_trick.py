import re

ACCESSORY_KEYWORDS = [
    r"\bpulseira\b", r"\bstrap\b", r"\bband\b", r"\bbracelet\b",
    r"\bcaixa vazia\b", r"\bempty\s+(?:watch\s+)?box\b", r"\bdisplay case\b",
    r"\bbox only\b", r"\bcase only\b", r"\bferramenta\b",
    r"\btool\b", r"\bpeça de reposição\b", r"\bspare part\b", r"\bfecho\b", r"\bbuckle\b"
]

def is_accessory_trick(title: str, main_query: str) -> bool:
    title_lower = title.lower()
    query_lower = main_query.lower()

    if any(k in query_lower for k in ["pulseira", "strap", "band", "caixa", "ferramenta"]):
        return False

    is_watch_search = any(w in query_lower for w in ["relogio", "relógio", "watch", "cronografo", "cronógrafo"])
    if not is_watch_search:
        return False

    for pattern in ACCESSORY_KEYWORDS:
        if re.search(pattern, title_lower):
            if any(k in pattern for k in ["vazia", "only", "empty", "display case"]):
                return True
            if not any(w in title_lower for w in ["watch", "relógio", "relogio"]):
                return True
            # Title begins with strap / band
            if re.search(r"^(?:nova\s+|luxo\s+|vintage\s+)?(?:pulseira|strap|band|bracelet)\b", title_lower.strip()):
                return True
            # Strap specifically for a watch brand or watch
            if re.search(r"\b(?:pulseira|strap|band|bracelet)\s+(?:for|para)\s+", title_lower):
                return True
            if re.search(r"\b(?:pulseira|strap|band|bracelet)\s+de\s+(?:rel[oó]gio|smartwatch|watch|apple|samsung|garmin|xiaomi|amazfit|seiko|rolex|casio)", title_lower):
                return True
            # English 'watch strap', 'watch band'
            if re.search(r"(?:watch|relógio|relogio)\s+(?:strap|band|bracelet)\b", title_lower):
                return True
            # Tools, spare parts, buckles for watches
            if pattern in [r"\bferramenta\b", r"\btool\b", r"\bpeça de reposição\b", r"\bspare part\b", r"\bfecho\b", r"\bbuckle\b"]:
                if re.search(rf"{pattern}\s+(?:for|para|de)\s+", title_lower):
                    return True

    return False
