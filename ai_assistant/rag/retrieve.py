from rag.lecture_manager import ensure_lecture_indexed, extract_youtube_video_id
from rag.embedder import get_embedding
from rag.vector_store import vector_store


async def retrieve_context(lecture_id: str, query: str, top_k: int = 3) -> str:
    """Performs end-to-end semantic retrieval for a user question against a specific lecture context."""
    if not lecture_id or not query:
        return ""

    indexed = await ensure_lecture_indexed(lecture_id)
    if not indexed:
        return ""

    video_id = extract_youtube_video_id(lecture_id)
    index_id = video_id if video_id else lecture_id

    query_emb = await get_embedding(query)
    relevant_chunks = vector_store.query(
        lecture_id=index_id,
        query_emb=query_emb,
        top_k=top_k
    )

    return "\n\n".join(relevant_chunks)
