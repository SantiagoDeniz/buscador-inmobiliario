import unicodedata


def stemming_basico(palabra: str) -> str:
    try:
        palabra = str(palabra)
    except Exception:
        return ""
    sufijos = ['oso', 'osa', 'idad', 'cion', 'sion', 'ero', 'era', 'ado', 'ada']
    for sufijo in sufijos:
        # Permite recortar si la base resultante tiene al menos 3 caracteres
        if palabra.endswith(sufijo) and len(palabra) >= len(sufijo) + 3:
            return palabra[:-len(sufijo)]
    return palabra


def extraer_variantes_keywords(keywords_filtradas):
    variantes = []
    if not keywords_filtradas:
        return variantes
    for kw in keywords_filtradas:
        if isinstance(kw, dict):
            t = kw.get('texto')
            if t:
                variantes.append(str(t))
            for s in kw.get('sinonimos', []) or []:
                if s:
                    variantes.append(str(s))
        else:
            variantes.append(str(kw))
    seen = set()
    unicos = []
    for v in variantes:
        if v not in seen:
            seen.add(v)
            unicos.append(v)
    return unicos


def build_keyword_groups(keywords_filtradas):
    """Convierte la salida de procesar_keywords en grupos de variantes.

    Cada grupo representa 1 palabra clave lógica (OR entre variantes: texto + sinónimos).
    El matching debe ser AND entre grupos, OR dentro del grupo.
    """
    groups = []
    if not keywords_filtradas:
        return groups
    for kw in keywords_filtradas:
        if isinstance(kw, dict):
            variants = []
            t = kw.get('texto')
            if t:
                variants.append(str(t))
            for s in (kw.get('sinonimos') or []):
                if s:
                    variants.append(str(s))
            # de-dup preservando orden
            seen = set()
            dedup = []
            for v in variants:
                if v not in seen:
                    seen.add(v)
                    dedup.append(v)
            if dedup:
                groups.append(dedup)
        else:
            groups.append([str(kw)])
    return groups
