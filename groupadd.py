#! /usr/bin/env python3
#################################################################################
#     File Name           :     groupadd.py
#     Created By          :     Eloi Silva
#     Creation Date       :     [2018-07-12 19:21]
#     Last Modified       :     [2018-07-16 19:38]
#     Description         :      
#################################################################################

import os, sys
import argparse, ldap3
from ldap3 import Server, Connection, ALL
from getpass import getpass

server = '127.0.0.1'
port = 389
base = 'dc=soc'
usuarios = 'ou=usuarios,{base}'.format(base=base)
grupos = 'ou=grupos,{base}'.format(base=base)

# Argument Parser
DESC = 'Add/Delete/Change LDAP Group'
USAGE = '''groupadd-ldap -h
groupadd-ldap -r group # Remove a empty group
groupadd-ldap -n group # Create a new group
groupadd-ldap -d -u username group # Delete a username from a group
groupadd-ldap -a -u username group # Add a username to a group
groupadd-ldap -D binddn
groupadd-ldap -w bindpw
'''

parser = argparse.ArgumentParser(usage=USAGE, description=DESC)

# Group of arguments
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-r', '--remove-group', dest='modify', action='store_true', help='Delete a group without members')
group.add_argument('-n', '--new-group', dest='modify', action='store_true', help='Create a new group')
group.add_argument('-d', '--delete-user', dest='modify', action='store_true', help='Remove user as group member')
group.add_argument('-a', '--add-user', dest='modify', action='store_true', help='Add user as group member')

default_user = 'cn={user},{ou}'.format(user=os.environ.get('USER'), ou=usuarios)
parser.add_argument('-u', '--user', default=default_user)
parser.add_argument('-D', '--binddn')
parser.add_argument('-w', '--bindpw')

args = parser.parse_args()

class Config:
    def __init__(self):
        self.user_config = os.path.join(os.environ.get('HOME'), '.ldap')
        Config.check_configfile(self.user_config)

    @staticmethod
    def check_configfile(user_config):
        if not os.path.isfile(user_config):
            from textwrap import dedent
            print('Configuration file not found\nPlease configure the file %s as bellow:' % user_config)
            config_example = dedent('''
                # Required
                [ldap]
                base = dc=soc
                server = 127.0.0.1
                port = 389
                ou_groups = ou=grupos,dc=soc

                [user]
                username = cn=a0046772,ou=usuarios,dc=soc
                # Optional
                ; This information will be asked it not found in this file
                password = secret
            ''')
            print(config_example.lstrip())
            sys.exit(1)

config = Config()
server = Server(server, port=port, get_info=ALL)
conn = Connection(server, user=usuario, password=senha)

def connect():
    if conn.bind():
        return conn
    else:
        print('Usuario ou senha invalido: %s' % conn.result)
        return False
