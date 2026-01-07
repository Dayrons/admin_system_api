from models.base import BaseModel
from sqlalchemy import Column,  String,ForeignKey,Integer
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from models.base import BaseModel





class HistoryService(BaseModel):
    __tablename__ = "historys"
    name = Column(String(255), nullable=False)


    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    service = relationship("Service", back_populates="histories")
    
    
