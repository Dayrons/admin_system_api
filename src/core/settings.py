from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    
    APP_NAME:str = "Orquestador de Servicios"

    DB_PATH: str = "/home/user/Documentos/Plansuarez/admin_system_api_ps/src/database.db"
    
    XMLRPC_DESTINATION_DIR:str = " /opt/xmlrpc"
    
    SECRET_KEY:str = "TU_LLAVE_SECRETA_SUPER_SEGURA"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    PYTHON_ENV_DIR: str = "/home/dayrons/Documentos/Plansuarez/odoo17/venv/bin/python3"

    @property
    def DATABASE_URL(self) -> str:
        abs_path = os.path.abspath(self.DB_PATH)
        return f"sqlite:////{abs_path}"

settings = Settings()