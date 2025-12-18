
<!-- Cambiar el usuario al usuario root influye en el uso de la carpeta -->
sudo chown -R tu_usuario:tu_usuario /home/user/Documentos/Plansuarez/admin_system_api_ps/

chmod -R 755 /home/user/Documentos/Plansuarez/admin_system_api_ps/

# Ir a la carpeta src donde está la DB
cd /home/user/Documentos/Plansuarez/admin_system_api_ps/src/

# Dar permisos de escritura al archivo
chmod 666 database.db

# Dar permisos de escritura a la carpeta (necesario para el bloqueo de archivos de SQLite)
chmod 777 .


sudo visudo

<!-- Se supone que este comando te asigna para que no te pida contrase;a al intentar manipular los system -->
tu_usuario ALL=(ALL) NOPASSWD: /usr/bin/mv /tmp/*.service /etc/systemd/system/, /usr/bin/systemctl daemon-reload, /usr/bin/systemctl enable *, /usr/bin/systemctl start *

Objetivo,Comando,Por qué
Carpeta de Scripts,chmod 755,Permite que Python guarde los archivos .py.
Archivo SQLite,chmod 666,Permite que SQLAlchemy inserte los registros.
Comandos Systemctl,visudo,Permite activar los servicios desde el código.


<!-- Hay que crear el proyecto con los mismos permisos que se crea odoo -->
<!-- cre la carpeta de forma manual con el usuario normal pero hay que ver en que puede influir con la ejecucion de los xmlrpc -->

<!-- Tener el cuenta que los xmlrpc no se ejecutan como super usuario ya que odoo es el encargado de la funcion -->
<!-- Tener en cuenta si en realidad se requiere utilizar el usuario sudo ya que se podria manipular los xmlrpc sin super usuario -->
sudo mkdir -p /opt/xmlrpc

sudo chown $USER:$USER /opt/xmlrpc

chmod 755 /opt/xmlrpc


<!-- No a todos los archivos se le debe crea un system ya que no todos deben de quedar en ejecucion constante -->