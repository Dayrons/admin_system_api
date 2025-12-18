from fastapi import APIRouter,Depends, UploadFile, Form,File,status, HTTPException
from sqlalchemy.orm import Session
from management_system.utils.functions import run_command
from management_system.schema.service_schema import Service, ServiceCreate
from dependencies.db_session import get_db
from management_system.services import system
import json

router = APIRouter(
    prefix="/v1/services",
    tags=["Content"]
)


@router.get("/", response_model=list[Service])
def get_all_services(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    return system.get_all_services(db, skip=skip, limit=limit)


@router.post("/")
async def manage_service(data: dict):
    if data.get("action") not in ["start", "stop", "restart", "status"]:
        raise HTTPException(status_code=400, detail="Acción no válida")

    result = run_command(["sudo", "systemctl", data.get("action"), data.get("service")])
    if result.returncode == 0:
        return {"message": f"Servicio {data.get("action")} ejecutado correctamente"}
    else:
        raise HTTPException(status_code=500, detail=f"Error: {result.stderr}")



@router.post("/deploy",response_model=Service, status_code=status.HTTP_201_CREATED)
async def deploy_service(service_in_json: str = Form(...),  file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    try:
        service_data = json.loads(service_in_json) 

        service_in = ServiceCreate(**service_data)
        
        return system.deploy_service(db=db,file=file,service_in=service_in)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el despliegue: {str(e)}")


