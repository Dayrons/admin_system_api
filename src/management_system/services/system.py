from sqlalchemy.orm import Session
from management_system.models.service import Service
from management_system.models.history_service import HistoryService
from management_system.schema.service_schema import ServiceCreate
from fastapi import HTTPException
from typing import List
import shutil
from core.settings import settings
import subprocess
import os

from management_system.utils.functions import run_command
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
caracas_tz = ZoneInfo("America/Caracas")

def get_all_services(db: Session, skip: int = 0, limit: int = 100) -> List[Service]:
    
    if limit > 200:
        limit = 200
    
    results = db.query(Service).offset(skip).limit(limit).all()
    
    
    for service in results:
        system_result = run_command(["sudo", "/usr/bin/systemctl", "is-active", service.name, "--no-pager"])
        # print(system_result)
        # print(f"system_result.stdout: {system_result.stdout}")
        # print(f"system_result.stderr: {system_result.stderr}")
        # print(f"system_result.returncode: {system_result.returncode}")
        service.is_active = True if system_result.stdout.strip() == "active" else False
        
        system_result = run_command([
            "sudo", "/usr/bin/journalctl", 
            "-u", service.name,      
            "-n", "20",              
            "--no-pager"             
        ])

        # print(f"journalctl stdout: {system_result.stdout}")
        # print(f"journalctl stderr: {system_result.stderr}")
    
    return results


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
        
        
        
        service_db = db.query(Service).filter(Service.name == service_name).first()
        
        if service_db:
            service_db.is_active = is_active
            history = HistoryService(
                name="iniciado" if is_active else "detenido",
                service=service_db
            )
            if hasattr(service_db, "updated_at"):
                service_db.updated_at = datetime.now(caracas_tz)
            service_db.histories.append(history)
            db.commit()  
            db.refresh(service_db)  # Recargamos el objeto actualizado
        else:
            print(f"Advertencia: El servicio {service_name} no existe en la base de datos.")

        return {
            "message": f"Servicio {action} ejecutado y actualizado en DB",
            "service": {
                "id": service_db.id if service_db else None,
                "name": service_name,
                "is_active": is_active,
                "histories":service_db.histories
            }
        }
    else:
        raise HTTPException(status_code=500, detail=f"Error de sistema: {result.stderr}")
    
    
def deploy_service(db: Session, service_in: ServiceCreate, file) -> Service:
    service_name = service_in.name
    if service_in.add_file:
        service_name = service_in.name.lower().replace(" ", ".")
        script_path = os.path.join(settings.XMLRPC_DESTINATION_DIR, file.filename)
        service_in.file_name = file.filename
        service_file_path = f"/etc/systemd/system/{service_name}.service"

        
        with open(script_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        if service_in.replay:
            #En el usuario debe de ir el usuario que tiene permisos para ejecutar el entorno virtual de odoo
            service_content = f"""[Unit]
                Description={service_in.description}
                After=network.target

                [Service]
                Type=simple
                Restart=always
                RestartSec=5
                SyslogIdentifier={service_name}
                User={service_in.user_exec}
                Group={service_in.user_exec}
                WorkingDirectory={settings.XMLRPC_DESTINATION_DIR}
                Environment=PYTHONUNBUFFERED=1
                ExecStart={settings.PYTHON_ENV_DIR} {script_path}
                StandardOutput=journal+console
                
                [Install]
                WantedBy=multi-user.target
            """

            with open(f"/tmp/{service_name}.service", "w") as f:
                f.write(service_content)

            subprocess.run(["sudo", "mv", f"/tmp/{service_name}.service", service_file_path], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
            subprocess.run(["sudo", "systemctl", "start" if service_in.is_active else "stop", service_name], check=True)
            
    # subprocess.run(["sudo", "systemctl", "status", service_name],check=True)
    
    service_in.name = service_name 
    
    service_db = Service(**service_in.model_dump())
    service_db.histories.append(HistoryService(name="servicio creado", service=service_db))
    db.add(service_db)
    db.commit()
    db.refresh(service_db)
    return service_db

    
def remove_service(db: Session, service_in: Service):
    """
    Detiene, deshabilita y remueve la unidad systemd, recarga systemd, resetea fallos,
    remueve posibles archivos xmlrpc guardados en settings.XMLRPC_DESTINATION_DIR
    y elimina el registro en la DB si existe.

    """
    if service_in.add_file:
        base_name = service_in.name[:-8] if service_in.name and service_in.name.endswith(".service") else service_in.name
        unit_name = f"{base_name}.service"
        unit_path = f"/etc/systemd/system/{unit_name}"

        steps = [
            (["sudo", "/usr/bin/systemctl", "stop", unit_name], "stop"),
            (["sudo", "/usr/bin/systemctl", "disable", unit_name], "disable"),
            (["sudo", "rm", "-f", unit_path], "remove unit file"),
            (["sudo", "/usr/bin/systemctl", "daemon-reload"], "daemon-reload"),
            (["sudo", "/usr/bin/systemctl", "reset-failed"], "reset-failed"),
        ]

        for cmd, desc in steps:
            result = run_command(cmd)
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Error al ejecutar '{' '.join(cmd)}' ({desc}): {result.stderr}")

        removed_file = ''
        try:
            dest_dir = settings.XMLRPC_DESTINATION_DIR
        except Exception:
            dest_dir = None

        if dest_dir and os.path.isdir(dest_dir):
            fname = getattr(service_in, "file_name", None)
            fpath = os.path.join(dest_dir, fname)
            run_command(["sudo", "rm", "-f", fpath])
            if not os.path.exists(fpath):
                removed_file = fpath
                
    db_deleted = False
    if getattr(service_in, "id", None) is not None:
        service_db = db.get(Service, service_in.id)
        if service_db:
            db.delete(service_db)
            db.commit()
            db_deleted = True
    else:

        service_db = db.query(Service).filter(Service.name == base_name).first()
        if service_db:
            db.delete(service_db)
            db.commit()
            db_deleted = True

    return {
        "message": f"Servicio '{unit_name}' removido del sistema y DB (si existía).",
        "unit_removed": unit_path,
        "xmlrpc_removed": removed_file,
        "db_deleted": db_deleted,
        "service_id": getattr(service_in, "id", None),
        "service_name": service_in.name
    }


def get_details(db: Session, service_id: int):
    service = db.query(Service).get(service_id)
    if not service:
        return {"error": "Servicio no encontrado en la base de datos", "status": 404}

    command = [
        "sudo", "/usr/bin/journalctl", 
        "-u", service.name, 
        "-n", "100", 
        "--no-pager"
    ]
    
    result = run_command(command)
    
    if result.returncode != 0:
        return {
            "service": service.name,
            "logs": "No se pudieron obtener los logs", 
            "error": result.stderr
        }
    
    return {
        "service": service.name,
        "logs": result.stdout,
        "history":[]
    }