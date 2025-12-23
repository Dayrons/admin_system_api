from sqlalchemy.orm import Session
from management_system.models.service import Service
from management_system.schema.service_schema import ServiceCreate
from fastapi import HTTPException
from typing import List
import shutil
from core.settings import settings
import subprocess
import os

from management_system.utils.functions import run_command


def get_all_services(db: Session, skip: int = 0, limit: int = 100) -> List[Service]:
    
    if limit > 200:
        limit = 200
    
    return db.query(Service).offset(skip).limit(limit).all()

# def management_service(data:dict):
#     if data.get("action") not in ["start", "stop", "restart", "status"]:
#         raise HTTPException(status_code=400, detail="Acción no válida")
#     result = run_command(["sudo", "/usr/bin/systemctl", data.get("action"), data.get("service")])
#     if result.returncode == 0:
#         return {"message": f"Servicio {data.get("action")} ejecutado correctamente", "result":result}
#     else:
#         raise HTTPException(status_code=500, detail=f"Error: {result.stderr}")
    

def management_service(data: dict, db: Session):
    action = data.get("action")
    service_name = data.get("service")
    
    # 1. Validar la acción
    if action not in ["start", "stop", "restart", "status"]:
        raise HTTPException(status_code=400, detail="Acción no válida")

    # 2. Ejecutar el comando en el sistema
    result = run_command(["sudo", "/usr/bin/systemctl", action, service_name])

    if result.returncode == 0:
        # 3. Determinar el nuevo estado
        is_active = True if action in ["start", "restart"] else False
        
        # 4. Actualizar en la Base de Datos
        # Buscamos el registro del servicio (ajusta 'name' según tu columna)
        db_service = db.query(Service).filter(Service.name == service_name).first()
        
        if db_service:
            db_service.is_active = is_active
            db.commit() # Guardamos los cambios
            db.refresh(db_service) # Recargamos el objeto actualizado
        else:
            # Opcional: Si el servicio no está en la DB, puedes decidir si ignorar o lanzar error
            print(f"Advertencia: El servicio {service_name} no existe en la base de datos.")

        # 5. Retornar la respuesta con el objeto de la DB
        return {
            "message": f"Servicio {action} ejecutado y actualizado en DB",
            "service": {
                "id": db_service.id if db_service else None,
                "name": service_name,
                "is_active": is_active
            }
        }
    else:
        raise HTTPException(status_code=500, detail=f"Error de sistema: {result.stderr}")
    
    

def deploy_service(db: Session, service_in: ServiceCreate, file) -> Service:
    service_name = service_in.name
    if service_in.add_file:
        service_name = service_in.name.lower().replace(" ", ".")
        script_path = os.path.join(settings.XMLRPC_DESTINATION_DIR, file.filename)
        service_file_path = f"/etc/systemd/system/{service_name}.service"

        
        with open(script_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        if service_in.replay:
            service_content = f"""[Unit]
                Description={service_in.description}
                After=network.target

                [Service]
                Type=simple
                WorkingDirectory={settings.XMLRPC_DESTINATION_DIR}
                ExecStart=/usr/bin/python3 {script_path}
                Restart=always
                User=root

                [Install]
                WantedBy=multi-user.target
            """

            with open(f"/tmp/{service_name}.service", "w") as f:
                f.write(service_content)

            subprocess.run(["sudo", "mv", f"/tmp/{service_name}.service", service_file_path], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
            subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
            
    subprocess.run(["sudo", "systemctl", "status", service_name],check=True)
    
    service_in.name = service_name 
    
    service_db = Service(**service_in.model_dump())
    db.add(service_db)
    db.commit()
    db.refresh(service_db)
    return service_db

    
