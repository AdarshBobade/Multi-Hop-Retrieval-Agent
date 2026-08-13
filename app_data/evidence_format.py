from app_data.models import Evidence

def format_evidence(evidence : list[Evidence]) -> str:
    formatted = []

    

    for item in evidence:

        
        lines = [   f"[EVIDENCE {item.citation_id}]",
                    f"Source type: {item.source_type}"]

        if item.source_type == "document":

            lines.extend([
                f"Source: {item.source}",
                f"Page: {item.page}" if item.page is not None else "Page: unknown",
                f"Document ID: {item.doc_id}" if item.doc_id else "",
                f"Chunk ID: {item.chunk_id}" if item.chunk_id else "",
            ])

        elif item.source_type == "web":

            lines.extend([
                f"Title: {item.title}" if item.title else "",
                f"URL: {item.url}" if item.url else "",
                f"Published: {item.published_date}" if item.published_date else "",
            ])

        lines.extend(["",
                    "Content:",
                    item.content
                    ])

        formatted.append("\n".join(line for line in lines if line))

    return "\n\n".join(formatted)