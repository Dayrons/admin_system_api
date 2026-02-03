from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    
    APP_NAME:str = "Orquestador de Servicios"

    DB_PATH: str = "/opt/exec/database.db"
    
    XMLRPC_DESTINATION_DIR:str = "/opt/xmlrpc"
    
    SECRET_KEY:str = "ZhJYkG8XrFtltCwrj-2s8vwR0lrgmLVUeaN87MAJq26RX-kceE2hunO4yAfrCcMH"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    PYTHON_ENV_DIR: str = "/opt/odoo16com/odoo-venv/bin/python3"

    @property
    def DATABASE_URL(self) -> str:
        abs_path = os.path.abspath(self.DB_PATH)
        return f"sqlite:////{abs_path}"

settings = Settings()