from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    
    APP_NAME:str

    DB_PATH: str = "database.db"
    
    XMLRPC_DESTINATION_DIR:str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        abs_path = os.path.abspath(self.DB_PATH)
        return f"sqlite:////{abs_path}"

settings = Settings()