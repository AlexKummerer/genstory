import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "GenStoryAI"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    SECRET_KEY: str = os.getenv("SECRET_KEY")

    class Config:
        env_file = ".env"


settings = Settings()

if __name__ == "__main__":
    print(f"Loaded APP_NAME: {settings.APP_NAME}")
    print(f"Loaded DATABASE_URL: {settings.DATABASE_URL}")
    print(f"Loaded OPENAI_API_KEY: {settings.OPENAI_API_KEY}")
