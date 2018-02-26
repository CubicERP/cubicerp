GUIDE OF INSTALLATION CUBICERP IN UBUNTU
=======================================

Installation of Python libraries

    $ sudo apt-get update
    $ sudo apt-get install python3-pip python3-babel python3-decorator python3-docutils python3-gevent python3-greenlet python3-html2text python3-jinja2 python3-lxml python3-mako python3-markupsafe python3-mock python3-ofxparse python3-passlib python3-psutil python3-pydot python3-pyparsing python3-pypdf2 python3-dateutil python3-yaml python3-tz python3-reportlab python3-requests python3-six python3-vatnumber python3-werkzeug python3-xlsxwriter python3-xlrd
    $ sudo pip3 install suds-py3 ebaysdk feedparser num2words Pillow psycopg2 pyldap pyserial pyusb qrcode vobject xlwt  
    $ wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.1/wkhtmltox-0.12.1_linux-trusty-amd64.deb
    $ sudo dpkg -i wkhtmltox-0.12.1_linux-trusty-amd64.deb
    $ sudo apt-get install -f
    $ sudo apt-get install npm
    $ sudo ln -s /usr/bin/nodejs /usr/bin/node
    $ sudo apt-get install node-less

Creation of the database user

    $ sudo su - postgres
    $ createuser -d -R -S cubicerp
    $ exit

User creation that will contain the synchronized branch

    $ sudo useradd cubicerp -m -s /bin/bash
    $ sudo su - cubicerp

Repository download

    $ git clone https://github.com/CubicERP/cubicerp
    $ cd cubicerp
    $ git checkout trunk

Generation of the configuration file

    $ ./cubicerp-server -s
    $ cp ~/.cubicerp_serverrc .

Modification of the configuration file (ports assignment)

    $ vi .cubicerp_serverrc
    -------------------------------------------
    [options]
    addons_path = ./odoo/addons,./addons
    ...
    data_dir = ./data
    -------------------------------------------
    $ ./cubicerp-server -c .cubicerp_serverrc 

Once started the service to test the installation, use the following URL:

    http://<ip-del-servidor>:8069
