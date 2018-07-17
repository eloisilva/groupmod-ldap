#! /usr/bin/env python3
#################################################################################
#     File Name           :     groupadd.py
#     Created By          :     Eloi Silva
#     Creation Date       :     [2018-07-12 19:21]
#     Last Modified       :     [2018-07-17 18:57]
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
group.add_argument('-r', '--remove-group', dest='modify', action='store_const', const='delete', help='Delete a group without members')
group.add_argument('-n', '--new-group', dest='modify', action='store_const', const='add', help='Create a new group')
group.add_argument('-d', '--delete-user', dest='modify', action='store_const', const='modify del', help='Remove user as group member')
group.add_argument('-a', '--add-user', dest='modify', action='store_const', const='modify add', help='Add user as group member')

parser.add_argument('-u', '--user', dest='user')
default_binddn = 'cn={user},{ou}'.format(user=os.environ.get('USER'), ou=usuarios)
parser.add_argument('-D', '--binddn', dest='binddn', default=default_binddn)
parser.add_argument('-w', '--bindpw', dest='bindpw')
parser.add_argument('group')


class Config:
    def __init__(self, parser):
        self.args = parser.parse_args()

    @property
    def changetype(self):
        return self.args.modify

    @property
    def user(self):
        if self.args.modify in ['modify del', 'modify add']:
            try:
                if usuarios in self.args.user:
                    return self.args.user
                else:
                    return 'cn=%s,%s' % (self.args.user, usuarios)
            except Exception:
                print('Error: -u user is required')
                os.exit(1)
        else:
            return None

    @property
    def group(self):
        if grupos in self.args.group:
            return self.args.group
        else:
            return 'cn=%s,%s' % (self.args.group, grupos)

    @property
    def binddn(self):
        return self.args.binddn

    @property
    def bindpw(self):
        if self.args.bindpw:
            return self.args.bindpw
        else:
            self.args.bindpw = getpass('%s password: ' % str(self.binddn))
            return self.args.bindpw


def connect(conn):
    if conn.bind():
        print(conn.result)
        return conn
    else:
        print('Usuario ou senha invalido: %s' % conn.result)
        return False

if __name__ == '__main__':
    config = Config(parser)
    server = Server(server, port=port, get_info=ALL)
    conn = Connection(server, user=config.binddn, password=config.bindpw)
    connect(conn)
