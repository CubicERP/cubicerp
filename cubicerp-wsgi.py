# WSGI Handler sample configuration file.
#
# Change the appropriate settings below, in order to provide the parameters
# that would normally be passed in the command-line.
# (at least conf['addons_path'])
#
# For generic wsgi handlers a global application is defined.
# For uwsgi this should work:
#   $ uwsgi_python --http :9090 --pythonpath . --wsgi-file cubicerp-wsgi.py
#
# For gunicorn additional globals need to be defined in the Gunicorn section.
# Then the following command should run:
#   $ gunicorn odoo:service.wsgi_server.application -c cubicerp-wsgi.py

import odoo

#----------------------------------------------------------
# Common
#----------------------------------------------------------
odoo.multi_process = True # Nah!

# Equivalent of --load command-line option
odoo.conf.server_wide_modules = ['web']
conf = odoo.tools.config

# Path to the OpenERP Addons repository (comma-separated for
# multiple locations)
#conf.parse_config(['-c','../.cubicerp_serverrc'])
#conf['addons_path'] = './addons,../ebranch,../community,../customize,../themes'
# Optional database config if not using local socket
#conf['db_name'] = 'mycompany'
#conf['db_host'] = 'localhost'
#conf['db_user'] = 'cubicerp'
#conf['db_port'] = 5432
#conf['db_password'] = ''
#conf['dbfilter']="^%d.*"
#conf['admin_passwd']="admin"
#conf['data_dir']='../data'

#----------------------------------------------------------
# Generic WSGI handlers application
#----------------------------------------------------------
application = odoo.service.wsgi_server.application

odoo.service.server.load_server_wide_modules()

#----------------------------------------------------------
# Gunicorn
#----------------------------------------------------------
# Standard OpenERP XML-RPC port is 8069
bind = conf['wsgi-bind']
pidfile = conf['wsgi-pidfile']
workers = conf['wsgi-workers']
timeout = conf['wsgi-timeout']
max_requests = conf['wsgi-max_requests']
preload_app = conf['wsgi-preload_app']

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
