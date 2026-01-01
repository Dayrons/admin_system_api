from pydantic import BaseModel
from datetime import datetime

class ServiceBase(BaseModel):
    name: str
    description:str
    status: str
    file_name: str | None = None
    is_active: bool
    add_file: bool
    replay:bool
    user_exec: str  = "root"
    

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    updated_at: datetime
    created_at: datetime
    class Config:
        from_attributes = True