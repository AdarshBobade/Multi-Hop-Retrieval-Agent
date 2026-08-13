from app_data.models import Evidence

def format_evidence(evidence : list[Evidence]) -> str:
    formatted = []

    

    for item in evidence:

        
        

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
            item.content
        ]

       

        formatted.append("\n".join(block))

    return "\n\n".join(formatted)