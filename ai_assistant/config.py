import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    app_title: str = "AI Lecture Assistant"
    app_version: str = "2.0"

    # Database Settings
    database_url: str = "sqlite+aiosqlite:///data/assistant.db"

    # Ollama Settings
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2"
    embedding_model: str = "nomic-embed-text"
    max_history_length: int = 10

    # Lecture Storage
    lecture_folder: str = "data/lectures"

    # Backend Settings
    backend_url: str = "http://localhost:5000"

    # Gemini Settings
    gemini_api_key: str = ""


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
