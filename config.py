# from dotenv import load_dotenv
# import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env'
    )
    MODE: str

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    CACHE_STORAGE_TIME: int
    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"



settings = Settings()

# load_dotenv()
#
# DB_NAME = os.environ.get('DB_NAME')
# DB_PORT = os.environ.get('DB_PORT')
# DB_HOST = os.environ.get('DB_HOST')
# DB_USER = os.environ.get('DB_USER')
# DB_PASS = os.environ.get('DB_PASS')
#
# CACHE_STORAGE_TIME = os.environ.get('CACHE_STORAGE_TIME')
# REDIS_HOST = os.environ.get('REDIS_HOST')
# REDIS_PORT = os.environ.get('REDIS_PORT')
#
# MODE = os.environ.get('MODE')
#
