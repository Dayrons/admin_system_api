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
                WorkingDirectory={settings.XMLRPC_DESTINATION_DIR}
                ExecStart={settings.PYTHON_ENV_DIR} {script_path}
                StandardOutput=journal+console
                User={service_in.user_exec}
                Group={service_in.user_exec}
                Restart=always
                RestartSec=5
                [Install]
                WantedBy=multi-user.target
            """

            with open(f"/tmp/{service_name}.service", "w") as f:
                f.write(service_content)

            subprocess.run(["sudo", "mv", f"/tmp/{service_name}.service", service_file_path], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
            subprocess.run(["sudo", "systemctl", "start" if service_in.replay else "stop", service_name], check=True)
            
    # subprocess.run(["sudo", "systemctl", "status", service_name],check=True)
    
    service_in.name = service_name 
    
    service_db = Service(**service_in.model_dump())
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

        # 1) Stop, disable, remove unit file, daemon-reload, reset-failed
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

        # # 2) Remover archivos xmlrpc en la carpeta destino (seguir guía de deploy_service)
        # removed_files = []
        # try:
        #     dest_dir = settings.XMLRPC_DESTINATION_DIR
        # except Exception:
        #     dest_dir = None

        # if dest_dir and os.path.isdir(dest_dir):
        #     # Intentar usar información del objeto recibido (service_in) primero
        #     possible_attrs = ("file_name", "filename", "script_name", "script", "xmlrpc_file", "path")
        #     for attr in possible_attrs:
        #         fname = getattr(service_in, attr, None)
        #         if fname:
        #             fpath = os.path.join(dest_dir, fname)
        #             run_command(["sudo", "rm", "-f", fpath])
        #             if not os.path.exists(fpath):
        #                 removed_files.append(fpath)

        #     # Si no se eliminó nada usando service_in, intentar obtener registro DB por id y revisar atributos
        #     try:
        #         db_record = db.get(Service, service_in.id) if getattr(service_in, "id", None) is not None else None
        #     except Exception:
        #         db_record = None

        #     if db_record:
        #         for attr in possible_attrs:
        #             fname = getattr(db_record, attr, None)
        #             if fname:
        #                 fpath = os.path.join(dest_dir, fname)
        #                 run_command(["sudo", "rm", "-f", fpath])
        #                 if not os.path.exists(fpath):
        #                     removed_files.append(fpath)

        #     # Como fallback, eliminar archivos que empiecen por el base_name (ej. base_name.py)
        #     for fname in os.listdir(dest_dir):
        #         if fname.startswith(base_name):
        #             fpath = os.path.join(dest_dir, fname)
        #             run_command(["sudo", "rm", "-f", fpath])
        #             if not os.path.exists(fpath):
        #                 removed_files.append(fpath)


    db_deleted = False
    if getattr(service_in, "id", None) is not None:
        db_service = db.get(Service, service_in.id)
        if db_service:
            db.delete(db_service)
            db.commit()
            db_deleted = True
    else:
        # Fallback: buscar por nombre base
        db_service = db.query(Service).filter(Service.name == base_name).first()
        if db_service:
            db.delete(db_service)
            db.commit()
            db_deleted = True

    return {
        "message": f"Servicio '{unit_name}' removido del sistema y DB (si existía).",
        "unit_removed": unit_path,
        # "xmlrpc_removed": removed_files,
        "db_deleted": db_deleted,
        "service_id": getattr(service_in, "id", None),
        "service_name": service_in.name
    }
