from pathlib import Path
from config import settings


def load_lecture(lecture_id: str) -> str | None:
    """Safely loads a lecture text file, preventing path traversal attacks."""
    if not lecture_id:
        return None

    safe_filename = Path(lecture_id).name
    base_dir = Path(settings.lecture_folder).resolve()
    file_path = (base_dir / f"{safe_filename}.txt").resolve()

    try:
        if not file_path.is_relative_to(base_dir):
            return None
    except ValueError:
        return None

    if not file_path.exists() or not file_path.is_file():
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
