import unicodedata

def normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

_RAW_SYNONYMS = {
    "safira": ["safira", "sapphire", "safir"],
    "sem logo": ["sem logo", "sem logotipo", "sterile", "sterile dial", "no logo", "unbranded", "sem marca", "liso", "simples"],
    "automatico": ["automatico", "automático", "automatic", "nh35", "nh36", "miyota"],
    "aço": ["aco", "aço", "stainless steel", "steel", "316l"],
    "infantil": ["infantil", "crianca", "criança", "kids", "children", "teen", "adolescente", "estudante", "aluno"],
}

SYNONYMS = {}
for syn_list in _RAW_SYNONYMS.values():
    for word in syn_list:
        SYNONYMS[normalize_text(word)] = syn_list

def matches_semantic_criteria(title: str, include_terms: list[str], exclude_terms: list[str]) -> bool:
    norm_title = normalize_text(title)

    for term in exclude_terms:
        norm_term = normalize_text(term.strip())
        if not norm_term:
            continue
        syns = SYNONYMS.get(norm_term, [norm_term])
        if any(normalize_text(s) in norm_title for s in syns):
            return False

    for term in include_terms:
        norm_term = normalize_text(term.strip())
        if not norm_term:
            continue
        syns = SYNONYMS.get(norm_term, [norm_term])
        if not any(normalize_text(s) in norm_title for s in syns):
            return False

    return True
