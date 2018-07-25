#! /usr/bin/env python3
#################################################################################
#     File Name           :     groupadd.py
#     Created By          :     Eloi Silva
#     Creation Date       :     [2018-07-12 19:21]
#     Last Modified       :     [2018-07-24 23:10]
#     Description         :      
#################################################################################

import os, sys
import argparse, ldap3
from ldap3 import Server, Connection, ALL, MODIFY_ADD, MODIFY_DELETE
from getpass import getpass

# Argument Parser
DESC = 'Add/Delete/Change LDAP Group'
USAGE = '''{progname} -h
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
        self.ou_users = 'ou=usuarios,{base}'.format(base=self.base)
        self.ou_groups = 'ou=grupos,{base}'.format(base=self.base)

    def add(self, conn):
        cn = self.group.split(',')[0]
        search = {
                'search_base': self.ou_groups,
                'search_filter': '(&(objectClass=posixGroup)(%s))' % cn
        }
        if not conn.search(**search):
            try:
                gid = self.nid_value(conn, self.ou_groups, 'gidNumber', 'posixGroup')
            except:
                print('[Error]  trying to get next gidNumber: ', conn.result)
            else:
                conn.add(self.group, 'posixGroup', {'gidNumber': gid})
                conn.search(**search)
                print('[Group add] -', conn.entries[0].entry_dn)
        else:
            print('[Error] : The group %s already existe' % self.group)

    def delete(self, conn):
        cn = self.group.split(',')[0]
        search = {
                'search_base': self.ou_groups,
                'search_filter': '(&(objectClass=posixGroup)(%s))' % cn,
                'attributes': 'gidNumber'
        }
        if conn.search(**search):
            gid = conn.entries[0].gidNumber.value
            search_0 = {
                    'search_base': self.ou_groups,
                    'search_filter': '(&(objectClass=posixGroup)(%s)(memberUid=*))' % cn,
                    'attributes': ['memberUid']
            }
            search_1 = {
                    'search_base': self.base,
                    'search_filter': '(&(objectClass=posixAccount)(gidNumber=%s))' % gid
            }
            if conn.search(**search_0):
                print('[Error] : Group with members, remove the memberUid before delete this group')
                print('  Members: %s' % conn.entries[0].memberUid.value)
            elif conn.search(**search_1):
                print('[Error] : Group with members, some user(s) has this group as primary group')
                print('    DN users:')
                for user in [u.entry_dn for u in conn.entries]: print('    %s' % user)
            else:
                conn.delete(self.group)
                if not conn.search(**search):
                    print('[Group deleted] -', self.group)
        else:
            print('[Error] : The group %s does not existe' % self.group)

    def del_member(self, conn):
        cn_group = self.group.split(',')[0]
        users = self.user_member(conn, self.ou_groups, self.user, cn_group, 'memberUid', member=True)
        change = {'memberUid': [(MODIFY_DELETE, users)]}
        if conn.search(self.ou_groups, '(&(objectclass=posixGroup)(%s))' % cn_group) and users:
            conn.modify(self.group, change)
            print('[Del members] - Group %s: %s' % (self.args.group, users))
            not_members = set(self.user) - set(users)
            if not_members:
                print('[Note] : User(s) is/are not member(s) of group %s: %s' (self.args.group, not_members))
        else:
            print('[Error] : User(s) is/are not member(s) of group %s: %s' % (self.args.group, self.user))

    def add_member(self, conn):
        cn_group = self.group.split(',')[0]
        users = self.user_member(conn, self.ou_groups, self.user, cn_group, 'memberUid', member=False)
        change = {'memberUid': [(MODIFY_ADD, users)]}
        if conn.search(self.ou_groups, '(&(objectclass=posixGroup)(%s))' % cn_group) and users:
            conn.modify(self.group, change)
            print('[Add members] - Group %s: %s' % (self.args.group, users))
            not_members = set(self.user) - set(users)
            if not_members:
                print('[Note] : User(s) already member(s) of group %s: %s' (self.args.group, not_members))
        else:
            print('[Error] : User(s) already member(s) of group %s: %s' % (self.args.group, self.user))

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
        #return self.dn(self.args.user, self.ou_users)
        return self.args.user.split(',')

    @property
    def group(self):
        return self.dn(self.args.group, self.ou_groups)

    @property
    def binddn(self):
        if not self.args.binddn:
            return 'cn={user},{ou}'.format(user=os.environ.get('USER'), ou=self.ou_users)
        else:
            return self.dn(self.args.binddn, self.ou_users)

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

    @staticmethod
    def nid_value(conn, base, attribute, objectclass):
        search = {
            'search_base': base,
            'search_filter': '(&(objectClass={obj})({attr}=*))'.format(obj=objectclass, attr=attribute),
            'attributes': [attribute]
        }
        conn.search(**search)
        return sorted([nid.gidnumber.value for nid in conn.entries])[-1] + 1

    @staticmethod
    def user_member(conn, base, users, group, attribute, member=True):
        def valida(func, **kargs):
            if member:
                if func(**kargs): return True
            else:
                if not func(**kargs): return True
        ans = []
        for user in users:
            search = {
                'search_base': base,
                'search_filter': '(&(objectClass=posixGroup)(%s)(%s=%s))' % (group, attribute, user),
                'attributes': [attribute]
            }
            if valida(conn.search, **search): ans.append(user)
        return ans

def connect(config):
    server = Server(config.server, port=config.port, get_info=ALL)
    conn = Connection(server, user=config.binddn, password=config.bindpw)
    if conn.bind():
        return conn
    else:
        print('Usuario ou senha invalido:')
        return False

if __name__ == '__main__':
    config = Config(parser)
    conn = connect(config)
    config.action(conn)
