from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from management_system.api.v1.routers.routers import api_router 
from auth.api.v1.routers.routers import api_router as auth_router 
from models.base import Base, engine
from core.settings import settings
from pathlib import Path
from auth.models.user import User
from auth.security import security



app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

def create_dir():
    path = Path(settings.XMLRPC_DESTINATION_DIR)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        


    

app.include_router(auth_router, prefix="/api") 
app.include_router(api_router, prefix="/api") 

if __name__ == "__main__":
    import uvicorn
    create_db_and_tables()
    create_dir()
    uvicorn.run(app, host="0.0.0.0", port=5000)


