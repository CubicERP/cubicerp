
GUIDE OF INSTALLATION CUBICERP IN UBUNTU
===========================================

Installation of Python libraries

    $ sudo apt-get update
    $ sudo apt-get install python-docutils python-gdata python-mako python-dateutil python-feedparser python-lxml python-tz python-vatnumber python-webdav python-xlwt python-werkzeug python-yaml python-zsi python-unittest2 python-mock python-libxslt1 python-ldap python-reportlab python-pybabel python-pychart python-simplejson python-psycopg2 python-vobject python-openid python-setuptools bzr postgresql unixodbc unixodbc-dev python-pyodbc python-psutil nginx git python-gevent language-pack-es tesseract-ocr tesseract-ocr-eng python-m2crypto libxml2-dev libxmlsec1-dev build-essential libssl-dev libffi-dev python-dev python-pip python-openpyxl python-numpy wkhtmltopdf-dbg
    $ sudo easy_install jinja2 CubicReport decorator requests pyPdf openerp-client-lib openerp-client-etl gunicorn passlib psycogreen pytesseract pycrypto qrcode
    $ sudo pip install --upgrade pip
    $ sudo pip install suds xmlsec cryptography boxsdk pyDNS cubicerp-client-etl
    $ sudo apt-get install -f

Creation of the database user

    $ sudo su - postgres
    $ createuser -d -R -S cubicerp
    $ exit

User creation that will contain the synchronized branch

    $ sudo useradd cubicerp -m -s /bin/bash
    $ sudo su - cubicerp

Download repositories, ask the name that was put to your private repository (<your_company>)

    $ git clone https://github.com/CubicERP/cubicerp
    $ cd cubicerp

Generation of the configuration file

    $ ./cubicerp-server -s
    $ cp ~/.cubicerp_serverrc .

Modification of the configuration file (ports assignment)

    $ vi .cubicerp_serverrc
    -------------------------------------------
    [options]
    addons_path = ./openerp/addons,./addons
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

Once started the service to test the installation, use the following URL:
    
    http://<ip-del-servidor>:8069

Commands to update the entire database:

    $ ./cubicerp-server -c .cubicerp_serverrc -d <base_de_datos> -u all -F
