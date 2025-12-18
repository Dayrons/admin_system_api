from sqlalchemy.orm import Session
from management_system.models.service import Service
from management_system.schema.service_schema import ServiceCreate
from fastapi import HTTPException
from typing import List
import shutil
from datetime import datetime
from core.settings import settings
import subprocess
import os


def get_all_services(db: Session, skip: int = 0, limit: int = 100) -> List[Service]:
    
    if limit > 200:
        limit = 200
    
    return db.query(Service).offset(skip).limit(limit).all()


def deploy_service(db: Session, service_in: ServiceCreate, file) -> Service:
   
    service_name = service_in.name.lower().replace(" ", "_")
    script_path = os.path.join(settings.XMLRPC_DESTINATION_DIR, file.filename)
    service_file_path = f"/etc/systemd/system/{service_name}.service"
    
    with open(script_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # service_content = f"""[Unit]
    #         Description={service_in.description}
    #         After=network.target

    #         [Service]
    #         Type=simple
    #         ExecStart=/usr/bin/python3 {script_path}
    #         Restart=always
    #         User=root

    #         [Install]
    #         WantedBy=multi-user.target
    #     """

    # # 4. Escribir el archivo .service (Requiere permisos de escritura)
    # # Nota: En un entorno real, podrías escribirlo en un temporal y luego moverlo con sudo
    # with open(f"/tmp/{service_name}.service", "w") as f:
    #     f.write(service_content)
    
    # # Mover a systemd y habilitar
    # subprocess.run(["sudo", "mv", f"/tmp/{service_name}.service", service_file_path], check=True)
    # subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
    # subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
    # subprocess.run(["sudo", "systemctl", "start", service_name], check=True)

    service_db = Service(**service_in.model_dump())
    db.add(service_db)
    db.commit()
    db.refresh(service_db)
    return service_db

    
