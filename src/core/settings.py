from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    
    APP_NAME:str = "Orquestador de Servicios"

    DB_PATH: str = "/opt/exec/database.db"
    
    XMLRPC_DESTINATION_DIR:str = "/opt/xmlrpc"
    
    SECRET_KEY:str = "mtMVzRrEGaCShaipSPVlkjv6LPDmxuzHDiegOMqZynX5GAg4JWcn7DeT87W5Git8"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    PYTHON_ENV_DIR: str = "/opt/usrodoo/venv/bin/python3"

    @property
    def DATABASE_URL(self) -> str:
        abs_path = os.path.abspath(self.DB_PATH)
        return f"sqlite:////{abs_path}"

settings = Settings()