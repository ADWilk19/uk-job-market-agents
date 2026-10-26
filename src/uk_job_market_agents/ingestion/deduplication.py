def deduplicate_postings(postings):
    """Return unique postings, preserving first-seen order."""
    seen = set()
    unique_postings = []

    for posting in postings:
        identity = (posting.source, posting.source_id)
        if identity in seen:
            continue
        seen.add(identity)
        unique_postings.append(posting)

    return unique_postings
