from typing import List


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 150) -> List[str]:
    """Splits a large text transcript into overlapping chunks of clean paragraphs/sentences."""
    if not text:
        return []

    text = " ".join(text.split())
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        
        if end < text_len:
            search_start = max(start, end - overlap)
            boundary = -1
            
            for punc in [". ", "? ", "! "]:
                pos = text.rfind(punc, search_start, end)
                if pos != -1:
                    boundary = max(boundary, pos + 1)
            
            if boundary == -1:
                boundary = text.rfind(" ", search_start, end)
                
            if boundary != -1:
                end = boundary + 1
        
        chunks.append(text[start:end].strip())
        start = end - overlap if end < text_len else text_len
        
        if start >= end:
            start = end
            
    return [c for c in chunks if len(c) > 20]
