import psycopg2 as pg
from sshtunnel import SSHTunnelForwarder
from settings import ssh_conf

from bs4 import BeautifulSoup
import requests
import psycopg2 as pg
import datetime
from random import choice
import time
import re
from sshtunnel import SSHTunnelForwarder
import sys
import os
import uuid

print("started")
#connecting to server

try:
    server = SSHTunnelForwarder(
            (ssh_conf['ssh_ip'], ssh_conf['ssh_port']),
            ssh_private_key=ssh_conf['ssh_private_key'],
            ssh_username=ssh_conf['ssh_user'],
            remote_bind_address=(ssh_conf['remote_bind_address'], ssh_conf['remote_bind_address_port'])
        )
    server.start()
    ssh_server_started = True    
    print ("server connected")
except Exception as ex:
#except:
    print ("server connection error")
    print (ex)
    ## print Exception to logfile

#connecting to db
try:   
    params = {
            'database': ssh_conf['ssh_db'],
            'user': ssh_conf['ssh_db_user'],
            'password': ssh_conf['ssh_db_pass'],
            'host': ssh_conf['ssh_db_host'],
            'port': server.local_bind_port
    }
    conn = pg.connect(**params)
    cursor = conn.cursor()
    print ("database connected")

except Exception as ex:
    print ("db error")
    print(ex)
    ## print to logfile

print("---------------------")
print("Good job man!")
print("---------------------")

conn.commit()
server.stop()
print("finished")