from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from core.settings import settings 
from datetime import datetime
from contextvars import ContextVar
from sqlalchemy import event
from sqlalchemy.orm import class_mapper
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    # Context variable to hold the current logged-in user (set this in request middleware)
    _current_user_ctx = ContextVar("current_user", default=None)

    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    delete  = Column(Boolean, default=False, nullable=False)

    @classmethod
    def set_current_user(cls, user_or_id):
        """
        Set the current user for the running context.
        Call this from your authentication/middleware code with either the user object or user id.
        """
        cls._current_user_ctx.set(user_or_id)

    @classmethod
    def get_current_user_id(cls):
        """
        Return the current user's id, or None if not set.
        Accepts either an integer id or an object with an 'id' attribute.
        """
        user = cls._current_user_ctx.get()
        if user is None:
            return None
        if isinstance(user, int):
            return user
        return getattr(user, "id", None)

    @classmethod
    def __declare_last__(cls):
        """
        Register mapper events to populate created_by and updated_by from the current user.
        This will be executed for each mapped subclass after mapping is complete.
        """
        try:
            mapper = class_mapper(cls)
        except Exception:
            # Not a mapped class (e.g. the abstract base), skip
            return

        def _before_insert(mapper, connection, target):
            uid = cls.get_current_user_id()
            if uid is not None:
                if getattr(target, "created_by", None) is None:
                    target.created_by = uid
                target.updated_by = uid

        def _before_update(mapper, connection, target):
            uid = cls.get_current_user_id()
            if uid is not None:
                target.updated_by = uid

        event.listen(mapper, "before_insert", _before_insert)
        event.listen(mapper, "before_update", _before_update)

        

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL 

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)


SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

