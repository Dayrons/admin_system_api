from pydantic import BaseModel
from datetime import datetime

class HistoryServiceBase(BaseModel):
    name: str
    

class HistoryServiceCreate(HistoryServiceBase):
    pass

class HistoryService(HistoryServiceBase):
    id: int
    updated_at: datetime
    created_at: datetime
    class Config:
        from_attributes = True