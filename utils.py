def format_project_label(raw_value: str | None) -> str:
    """Convert stored project identifier/domain into a human-friendly label."""
    if not raw_value:
        return "Wikipedia"

    domain = str(raw_value).strip()
    if not domain:
        return "Wikipedia"

    lowered = domain.lower()
    parts = lowered.split('.')
    first_part = parts[0] if parts else lowered
    second_level = parts[-2] if len(parts) >= 2 else lowered

    project_map = {
        'wikipedia': 'Wikipedia',
        'wiktionary': 'Wiktionary',
        'wikibooks': 'Wikibooks',
        'wikiquote': 'Wikiquote',
        'wikinews': 'Wikinews',
        'wikiversity': 'Wikiversity',
        'wikivoyage': 'Wikivoyage',
        'wikisource': 'Wikisource',
        'wikidata': 'Wikidata',
        'wikifunctions': 'Wikifunctions',
        'wikimediafoundation': 'Wikimedia Foundation',
        'metawiki': 'MetaWiki',
        'meta': 'MetaWiki',
        'wikicommons': 'Wikimedia Commons'
    }

    if second_level == 'wikimedia':
        meta_map = {
            'meta': 'MetaWiki',
            'commons': 'Wikimedia Commons',
            'incubator': 'Wikimedia Incubator'
        }
        if first_part in meta_map:
            return meta_map[first_part]
        return 'Wikimedia'

    if second_level in project_map:
        return project_map[second_level]

    cleaned = second_level.replace('-', ' ').replace('_', ' ').strip()
    if cleaned:
        return cleaned.title()

    return domain.title()
