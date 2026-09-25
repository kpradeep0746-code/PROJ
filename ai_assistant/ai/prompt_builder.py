import re
from sqlalchemy.ext.asyncio import AsyncSession
from ai.memory import get_history
from rag.retrieve import retrieve_context

CATEGORIES = {
    "Programming/Code": r"\b(code|program|function|class|method|syntax|language|script|variable|loop|array|pointer|object)\b",
    "Debugging": r"\b(bug|error|exception|fail|crash|debug|wrong|issue|incorrect|fix|why does this not work)\b",
    "Algorithm": r"\b(algorithm|sort|search|tree|graph|recursion|complexity|big o|nodes|stack|queue)\b",
    "Math": r"\b(math|equation|solve|formula|derivative|integral|calculate|matrix|sum|algebra|theorem)\b",
    "MCQ": r"\b(mcq|multiple choice|option [a-d]|correct option|which of the following)\b",
    "Interview/Viva/Exam": r"\b(interview|viva|exam|test|mock|oral|quiz|marks|question paper)\b",
    "Comparison": r"\b(compare|difference|vs|versus|distinguish|contrast|advantages and disadvantages)\b",
    "Summary": r"\b(summary|summarize|outline|brief|recap|tl;dr)\b",
    "Definition": r"\b(define|definition|what is|what are|meaning of|stands for)\b",
    "Explanation": r"\b(explain|explanation|how does|why does|tell me about|understand)\b"
}


def classify_question(question: str) -> str:
    """Classifies the user question into a specific educational type to optimize prompt template."""
    q_lower = question.lower()
    for category, pattern in CATEGORIES.items():
        if re.search(pattern, q_lower):
            return category
    return "Theory/General"


def get_system_prompt(category: str) -> str:
    """Returns an optimized system prompt guiding the LLM to give clean, structured, and modern markdown answers."""
    
    base_instructions = """You are a helpful and structured College AI Assistant. Your goal is to provide clean, clear, and premium formatted answers to student questions.

CRITICAL INSTRUCTIONS:
1. **Source Grounding**: Treat the provided video transcript/context as your primary source of truth. Analyze the video context first to see if the answer to the user's question is present.
2. **Graceful Fallback**: 
   - If the answer IS in the video context, answer directly based on it.
   - If the answer IS NOT in the video context (or the question is unrelated to the video), gracefully fall back to your general academic knowledge to provide the correct response. In this case, prefix your answer with: "*(Note: This is from general knowledge as it is not mentioned in the video)*" followed by your response.
3. **Structured Design & Formatting**:
   - Structure your output using Markdown to resemble responses from modern AI assistants (like ChatGPT, Gemini, or Claude).
   - Use clean paragraph spacing, proper headers, bullet points, numbered lists, highlighted keywords, code blocks when appropriate, tables where helpful, and quotes where appropriate.
   - If the response is long, automatically generate a concise summary at the top.
   - Dynamically organize answers into standard, logical sections where appropriate, such as:
     - `# Summary`
     - `# Explanation`
     - `# Key Points`
     - `# Examples`
     - `# Important Notes`
     - `# Conclusion`
"""

    category_tweaks = {
        "Programming/Code": (
            "\nFor Programming/Code questions:\n"
            "- Dynamically include the `# Summary`, `# Explanation`, and `# Examples` sections.\n"
            "- Ensure you include clean, commented, and compile-ready code blocks.\n"
            "- Use `# Important Notes` to highlight gotchas, syntax details, or best practices."
        ),
        "Debugging": (
            "\nFor Debugging questions:\n"
            "- Organize sections like `# Summary` (describing the error), `# Explanation` (root cause), and `# Examples` (the corrected code).\n"
            "- Clearly contrast the wrong code and the fixed code."
        ),
        "Algorithm": (
            "\nFor Algorithm questions:\n"
            "- Include `# Summary`, `# Explanation`, `# Key Points` (e.g. step-by-step logic), and `# Examples`.\n"
            "- In `# Important Notes`, detail the time/space complexity (Big O) and resource usage."
        ),
        "Math": (
            "\nFor Math questions:\n"
            "- Include `# Summary`, `# Explanation` (step-by-step breakdown of equations), and `# Examples`.\n"
            "- Ensure formula symbols and steps are cleanly aligned."
        ),
        "Comparison": (
            "\nFor Comparison questions:\n"
            "- Include `# Summary` and `# Explanation`.\n"
            "- Use markdown tables or bulleted `# Key Points` to compare/contrast concepts directly."
        )
    }

    tweak = category_tweaks.get(category, "\nDynamically structure sections to fit this academic topic.")
    return base_instructions + tweak


async def build_prompt(db: AsyncSession, student_id: str, lecture_id: str, question: str) -> list[dict]:
    """Retrieves relevant lecture context using RAG, classifies the query, and assembles the conversation history."""
    
    lecture_context = await retrieve_context(lecture_id, question, top_k=3)
    category = classify_question(question)
    system_prompt = get_system_prompt(category)

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    if lecture_context:
        messages.append({
            "role": "system",
            "content": (
                f"Verified Video Context from the Lecture Transcript:\n"
                f"\"\"\"\n{lecture_context}\n\"\"\"\n\n"
                f"Use this context as your primary source of truth. If the answer cannot be found in this context, "
                f"fall back to general academic knowledge and prefix your response with the general knowledge disclaimer."
            )
        })
    else:
        messages.append({
            "role": "system",
            "content": f"No lecture context found for this video. Answer the question using general academic knowledge."
        })

    history = await get_history(db, student_id)
    messages.extend(history)

    messages.append({
        "role": "user",
        "content": question
    })

    return messages

