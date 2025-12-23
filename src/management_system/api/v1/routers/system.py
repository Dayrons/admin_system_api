from fastapi import APIRouter,Depends, UploadFile, Form,File,status, HTTPException
from sqlalchemy.orm import Session
from management_system.schema.service_schema import Service, ServiceCreate
from dependencies.db_session import get_db
from management_system.services import system
from fastapi.security import OAuth2PasswordBearer
import json
from typing import Optional

router = APIRouter(
    prefix="/v1/services",
    tags=["System"]
)

oauth2 = OAuth2PasswordBearer(tokenUrl="login")


@router.get("/", response_model=list[Service])
def get_all_services(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2),
    skip: int = 0,
    limit: int = 100
):
    return system.get_all_services(db, skip=skip, limit=limit)


@router.post("/management")
async def management_service(data: dict, db: Session = Depends(get_db), token: str = Depends(oauth2),):
    return system.management_service(data, db=db)


@router.post("/deploy",response_model=Service, status_code=status.HTTP_201_CREATED)
async def deploy_service(service_in_json: str = Form(...),  file: Optional[UploadFile] = File(None), db: Session = Depends(get_db),  token: str = Depends(oauth2),):
    try:
        service_data = json.loads(service_in_json) 

        service_in = ServiceCreate(**service_data)
        
        return system.deploy_service(db=db,file=file,service_in=service_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el despliegue: {str(e)}")


