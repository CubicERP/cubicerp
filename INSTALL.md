GUIA DE INSTALACIÓN CUBICERP EN UBUNTU
======================================

Instalación de librerías Python

    $ sudo apt-get update
    $ sudo apt-get install python-docutils python-gdata python-mako python-dateutil python-feedparser python-lxml python-tz python-vatnumber python-webdav python-xlwt python-werkzeug python-yaml python-zsi python-unittest2 python-mock python-libxslt1 python-ldap python-reportlab python-pybabel python-pychart python-simplejson python-psycopg2 python-vobject python-openid python-setuptools bzr postgresql unixodbc unixodbc-dev python-pyodbc python-psutil nginx git python-gevent language-pack-es tesseract-ocr tesseract-ocr-eng python-m2crypto libxml2-dev libxmlsec1-dev build-essential libssl-dev libffi-dev python-dev python-pip python-openpyxl python-numpy wkhtmltopdf-dbg
    $ sudo easy_install jinja2 CubicReport decorator requests pyPdf openerp-client-lib openerp-client-etl gunicorn passlib psycogreen pytesseract pycrypto qrcode
    $ sudo pip install --upgrade pip
    $ sudo pip install suds xmlsec cryptography boxsdk pyDNS cubicerp-client-etl
    $ sudo apt-get install -f

Creación del usuario de base de datos

    $ sudo su - postgres
    $ createuser -d -R -S cubicerp
    $ exit

Creación de usuario que contendrá al branch sincronizado

    $ sudo useradd cubicerp -m -s /bin/bash
    $ sudo su - cubicerp
    
Descarga de repositorios, preguntar el nombre se le puso a su repositorio privado (<tu_empresa>)
    
    $ git clone https://github.com/CubicERP/cubicerp
    $ cd cubicerp
    ## Inicializa los submodulos ##
    $ git submodule init
    ## Actualiza los submodulos ##
    $ git submodule update
    
Para actualizar los repositorios poner los siguientes comandos:

    ## # Actualiza el directorio actual de su repositorio privado, es decir "cubicerp" ##
    ## $ git pull 
    ## Para abrir la versión estable del repositorio ##
    $ git checkout trunk
    $ git submodule foreach git checkout cubicerp
    ## Limpia posibles archivos temporales
    $ git clean -d -f
    $ git submodule foreach git clean -d -f

Generación del archivo de configuración

    $ cd ..
    $ cubicerp/cubicerp-server -s
    $ cp ~/.cubicerp_serverrc .


Modificación del archivo de configuración (asignación de puertos)

    $ vi .cubicerp_serverrc
    -------------------------------------------
    [options]
    addons_path = ./odoo/addons,./trunk,./branch,./community
    ...
    data_dir = ./data
    ...
    xmlrpc = True
    xmlrpc_interface =
    xmlrpc_port = 8069
    xmlrpcs = True
    xmlrpcs_interface =
    xmlrpcs_port = 8071
    -------------------------------------------


Los comandos para iniciar y parar el servicio del CubicERP en desarrollo con Werkzeugh

    $ ./stop.sh
    $ ./start.sh

Los comandos para iniciar y reiniciar el servicio del CubicERP en producción con gunicorn

    $ ./gstart.sh
    $ ./grestart.sh

Agregando inicio automatico del servicio

    $ sudo vi /etc/rc.local
    -------------------------------------------
    sudo su - cubicerp -c "cd cbc;./start.sh"
    sudo su - cubicerp -c "cd cbc;./gstart.sh"
    -------------------------------------------

Una vez iniciado el servicio para probar la instalación utilizar el siguiente url:

    http://<ip-del-servidor>:8069


Comandos para actualización  de toda la base de datos

    $ cd cbc
    $ cubicerp/cubicerp-server -c .cubicerp_serverrc -d <base_de_datos> -u all -F
