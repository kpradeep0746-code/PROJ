from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import ChatMessage
from config import settings


async def get_history(db: AsyncSession, student_id: str, limit: int = None) -> list[dict]:
    """Retrieves conversation history for a student from database, sorted by timestamp ascending."""
    if limit is None:
        limit = settings.max_history_length

    result = await db.execute(
        select(ChatMessage)
        .filter(ChatMessage.student_id == student_id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    messages = list(reversed(messages))
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


async def add_message(db: AsyncSession, student_id: str, role: str, content: str) -> ChatMessage:
    """Saves a chat message to the database."""
    message = ChatMessage(
        student_id=student_id,
        role=role,
        content=content
    )
    db.add(message)
    await db.flush()
    return message
