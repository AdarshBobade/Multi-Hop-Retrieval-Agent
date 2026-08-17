from app_data.models import Evidence

def format_evidence(
    evidence: list[Evidence],
    max_items: int = 10,
    max_chars_per_item: int = 1400,
    max_total_chars: int = 12000,
) -> str:
    formatted = []
    total_chars = 0

    for item in evidence[:max_items]:

        
        

        if item.source_type == "document":

            metadata = [
                f"Source: {item.source}",
                f"Page: {item.page}" if item.page is not None else None,
                f"Document ID: {item.doc_id}" if item.doc_id else None,
                f"Chunk ID: {item.chunk_id}" if item.chunk_id else None,
            ]

        elif item.source_type == "web":

             metadata = [
                f"Title: {item.title}" if item.title else None,
                f"URL: {item.url}" if item.url else None,
                f"Published: {item.published_date}"
                if item.published_date else None,
            ]


        block = [
            f"[EVIDENCE {item.citation_id}]",
            f"Source type: {item.source_type}",
            *[line for line in metadata if line],
            "",
            "Content:",
            item.content[:max_chars_per_item]
        ]

        formatted_block = "\n".join(block)
        remaining_chars = max_total_chars - total_chars
        if remaining_chars <= 0:
            break
        formatted_block = formatted_block[:remaining_chars]
        formatted.append(formatted_block)
        total_chars += len(formatted_block)

    return "\n\n".join(formatted)
