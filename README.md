# Admin System API

Pequeñas instrucciones para instalar, ejecutar y desplegar la API.

## Requisitos
- Python 3.8+
- Virtualenv (opcional)
- pyinstaller (si se crea ejecutable)
- systemd (para servicio)

## Usar el entorno virtual (recomendado)
1. Activar venv y instalar dependencias:
```bash
sudo ./venv/bin/python3 -m pip install -r requirements.txt
```
2. Ejecutar la aplicación:
```bash
sudo ./venv/bin/python3 ./src/main.py
```
Nota: se usa sudo porque la app escribe en directorios del sistema; si prefiere no usar root, ajuste permisos y rutas.

## Crear un ejecutable con PyInstaller
Genera un binario único para desplegar:
```bash
pyinstaller --onefile \
    --name admin_system_api \
    --add-data ".env:." \
    --paths . \
    --hidden-import="passlib.handlers.bcrypt" \
    --hidden-import=uvicorn.logging \
    --hidden-import=uvicorn.loops.auto \
    --hidden-import=uvicorn.protocols.http.h11_impl \
    src/main.py
```
El ejecutable resultante estará en `dist/admin_system_api`. Copiarlo a la ruta de ejecución deseada (ej. `/opt/exec/admin_system_api`).

## Servicio systemd (ejemplo)
Crear `/etc/systemd/system/admin_system_api.service` con:
```
[Unit]
Description=Servicio API Admin System
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/exec
ExecStart=/opt/exec/admin_system_api          # <-- ajustar según ubicación del ejecutable
Restart=always
RestartSec=5
StandardOutput=append:/var/log/admin_system_api.log
StandardError=append:/var/log/admin_system_api_error.log

[Install]
WantedBy=multi-user.target
```
Habilitar y arrancar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now admin_system_api.service
sudo systemctl  start admin_system_api.service
sudo journalctl -u admin_system_api -f
```

## Carpetas para XML-RPC
Crear la carpeta y ajustar permisos:
```bash
sudo mkdir -p /opt/xmlrpc
sudo chown $USER:$USER /opt/xmlrpc
sudo chmod 755 /opt/xmlrpc
```

## Logs y permisos
- Asegurarse de que el usuario que ejecuta el servicio tenga permisos de escritura en `/var/log/` o redirigir logs a una ruta accesible.
- Si no desea ejecutar como root, crear un usuario específico y ajustar `User=` y permisos de carpetas.

## Notas
- Mantener el archivo `.env` fuera del repositorio si contiene credenciales.
- Probar localmente antes de desplegar con systemd.
- Ajustar rutas y nombres según su entorno.
