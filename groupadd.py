#! /usr/bin/env python3
#################################################################################
#     File Name           :     groupadd.py
#     Created By          :     Eloi Silva
#     Creation Date       :     [2018-07-12 19:21]
#     Last Modified       :     [2018-07-19 01:29]
#     Description         :      
#################################################################################

import os, sys
import argparse, ldap3
from ldap3 import Server, Connection, ALL
from getpass import getpass

# Argument Parser
DESC = 'Add/Delete/Change LDAP Group'
USAGE = '''groupadd-ldap -h
{progname} -r group # remove a empty group
{progname} -n group # create a new group
{progname} -d -u member-user group # delete member-user from group
{progname} -a -u member-user group # add member-user to group
{progname} -D ldap-username # pass ldap dn to authenticate. Use $USER if option not given
{progname} -w ldap-password # pass ldap dn password. Ask for password if option not given
'''.format(progname=str(sys.argv[0]))

# Create argparse
parser = argparse.ArgumentParser(usage=USAGE, description=DESC)

# Authentication args
parser.add_argument('-D', '--binddn', dest='binddn', metavar='ldap-username')
parser.add_argument('-w', '--bindpw', dest='bindpw', metavar='ldap-password')

# Add/Remove user member arg
parser.add_argument('-u', '--user', dest='user', metavar='member-user')

# Required - Group positional 
parser.add_argument('group')

# Group of arguments
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-r', '--remove-group',
        dest='modify',
        action='store_const',
        const='delete',
        help='Delete a group without members'
        )
group.add_argument('-n', '--new-group',
        dest='modify',
        action='store_const',
        const='add',
        help='Create a new group'
        )
group.add_argument('-d', '--member-del',
        dest='modify',
        action='store_const',
        const='del_member',
        help='Remove user as group member'
        )
group.add_argument('-a', '--member-add',
        dest='modify',
        action='store_const',
        const='add_member',
        help='Add user as group member'
        )

class Config:
    def __init__(self, parser):
        self.args = parser.parse_args()
        self.server = '127.0.0.1'
        self.port = 389
        self.base = 'dc=soc'
        self.usuarios = 'ou=usuarios,{base}'.format(base=self.base)
        self.grupos = 'ou=grupos,{base}'.format(base=self.base)

    def add(self, conn):
        print(self.changetype, self.binddn, self.bindpw, self.group)

    def delete(self, conn):
        print(self.changetype, self.binddn, self.bindpw, self.group)

    def del_member(self, conn):
        print(self.changetype, self.binddn, self.bindpw, self.user, self.group)

    def add_member(self, conn):
        print(self.changetype, self.binddn, self.bindpw, self.user, self.group)

    def action(self, conn):
        act = self.__getattribute__(self.changetype)
        if act:
            act(conn)
        else:
            print('Action not implemented')

    @property
    def changetype(self):
        return self.args.modify

    @property
    def user(self):
        return self.dn(self.args.user, self.usuarios)

    @property
    def group(self):
        return self.dn(self.args.group, self.grupos)

    @property
    def binddn(self):
        if not self.args.binddn:
            return 'cn={user},{ou}'.format(user=os.environ.get('USER'), ou=self.usuarios)
        else:
            return self.dn(self.args.binddn, self.usuarios)

    @property
    def bindpw(self):
        if self.args.bindpw:
            return self.args.bindpw
        else:
            self.args.bindpw = getpass('(%s) password: ' % str(self.binddn))
            return self.args.bindpw

    @staticmethod
    def dn(cn, ou):
        if ou in cn:
            return cn
        else:
            return 'cn=%s,%s' % (cn, ou)

def connect(config):
    server = Server(config.server, port=config.port, get_info=ALL)
    conn = Connection(server, user=config.binddn, password=config.bindpw)
    if conn.bind():
        print('[Ok] LDAP Connected...')
        return conn
    else:
        #print('Usuario ou senha invalido: %s' % conn.result)
        print('Usuario ou senha invalido:')
        return False

if __name__ == '__main__':
    config = Config(parser)
    conn = connect(config)
    config.action(conn)
