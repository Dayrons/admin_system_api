from models.base import BaseModel
    
from sqlalchemy import Column,  String, Text, Boolean
from sqlalchemy.orm import    relationship


from models.base import BaseModel
from sqlalchemy.dialects.postgresql import ENUM

SERVICE_STATUS = ['activo', 'inactivo']
service_status_enum = ENUM(*SERVICE_STATUS, name='content_types', create_type=True)


class Service(BaseModel):
    __tablename__ = "services"

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    status = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False,default=False)
    add_file = Column(Boolean, nullable=False,default=False)
    file_name = Column(String(255), nullable=True)
    replay = Column(Boolean, nullable=False,default=False)
    user_exec = Column(String(255), nullable=False,default="root")
    histories = relationship("HistoryService", back_populates="service", cascade="all, delete-orphan")
    

