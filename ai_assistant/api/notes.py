from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

from database.models import PersonalNote
from api.deps import get_async_db

router = APIRouter()

class NoteCreate(BaseModel):
    student_id: str
    title: str
    content: str

class NoteUpdate(BaseModel):
    title: str
    content: str

class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: str
    title: str
    content: str
    created_at: str
    updated_at: str

@router.get("/api/notes", response_model=List[NoteResponse])
async def get_notes(
    student_id: str = Query(..., description="ID of the student"),
    q: Optional[str] = Query(None, description="Search query for title or content"),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieves all notes for a specific student, optionally filtered by a search query."""
    try:
        conditions = [PersonalNote.student_id == student_id]
        if q and q.strip():
            search_pattern = f"%{q.strip()}%"
            conditions.append(
                or_(
                    PersonalNote.title.like(search_pattern),
                    PersonalNote.content.like(search_pattern)
                )
            )
        
        stmt = select(PersonalNote).where(and_(*conditions)).order_by(PersonalNote.updated_at.desc())
        result = await db.execute(stmt)
        notes = result.scalars().all()
        
        return [
            NoteResponse(
                id=note.id,
                student_id=note.student_id,
                title=note.title,
                content=note.content,
                created_at=note.created_at.isoformat() if note.created_at else "",
                updated_at=note.updated_at.isoformat() if note.updated_at else ""
            )
            for note in notes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

@router.post("/api/notes", response_model=NoteResponse)
async def create_note(request: NoteCreate, db: AsyncSession = Depends(get_async_db)):
    """Creates a new note for a student."""
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Note title cannot be empty.")
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Note content cannot be empty.")

    try:
        new_note = PersonalNote(
            student_id=request.student_id,
            title=request.title,
            content=request.content
        )
        db.add(new_note)
        await db.commit()
        await db.refresh(new_note)
        
        return NoteResponse(
            id=new_note.id,
            student_id=new_note.student_id,
            title=new_note.title,
            content=new_note.content,
            created_at=new_note.created_at.isoformat() if new_note.created_at else "",
            updated_at=new_note.updated_at.isoformat() if new_note.updated_at else ""
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")

@router.put("/api/notes/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, request: NoteUpdate, db: AsyncSession = Depends(get_async_db)):
    """Updates an existing note."""
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="Note title cannot be empty.")
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Note content cannot be empty.")

    try:
        stmt = select(PersonalNote).where(PersonalNote.id == note_id)
        result = await db.execute(stmt)
        note = result.scalar_one_or_none()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found.")
        
        note.title = request.title
        note.content = request.content
        note.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(note)
        
        return NoteResponse(
            id=note.id,
            student_id=note.student_id,
            title=note.title,
            content=note.content,
            created_at=note.created_at.isoformat() if note.created_at else "",
            updated_at=note.updated_at.isoformat() if note.updated_at else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update note: {str(e)}")

@router.delete("/api/notes/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_async_db)):
    """Deletes an existing note."""
    try:
        stmt = select(PersonalNote).where(PersonalNote.id == note_id)
        result = await db.execute(stmt)
        note = result.scalar_one_or_none()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found.")
        
        await db.delete(note)
        await db.commit()
        
        return {"success": True, "message": "Note deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {str(e)}")
