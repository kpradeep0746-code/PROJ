from pydantic import BaseModel


class ChatRequest(BaseModel):
    student_id: str
    lecture_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
