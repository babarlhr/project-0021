import csv
import xmlrpclib
from datetime import datetime, timedelta
import pyodbc

username = 'admin'
password = 'P@ssw0rd'
dbname = 'demo_hrms_02'
sock_common = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/common')
sock_object = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')
uid = sock_common.login(dbname, username, password)

employee_args = [('nik', '=', row[0].strip())]
employee_ids = sock_object.execute(dbname, uid, password, 'hr.employee', 'search', employee_args)
