#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""OneLogin LDAP authentication."""

import argparse

import django
import os
import sys


django.setup()

from django.conf import settings
from djauth.managers import LDAPManager
from djimix.core.database import get_connection
from djimix.core.database import xsql

# set up command-line options
desc = """
    Maquette for OneLogin
"""

parser = argparse.ArgumentParser(
    description=desc, formatter_class=argparse.RawTextHelpFormatter,
)

parser.add_argument(
    '--username',
    dest='username',
    required=True,
    help="Person's username.",
)
parser.add_argument(
    '--password',
    dest='password',
    required=False,
    help="Person's password.",
)
parser.add_argument(
    '--test',
    action='store_true',
    help="Dry run?",
    dest='test',
)


def main():
    """Authenticate against OneLogin LDAP."""
    ldap_groups = settings.LDAP_GROUPS
    ldap_group_attr = settings.LDAP_GROUP_ATTR
    eldap = None
    try:
        eldap = LDAPManager()
    except Exception as error:
        raise Exception(error)

    if eldap:
        print("El Dap init")
        result_data = eldap.search(find=username, field='cn')
        print(result_data)
        if result_data:
            cid = result_data[0][1][settings.LDAP_ID_ATTR][0]
            print('cid = {0}'.format(cid))
            if password:
                print("attempting to bind...")
                try:
                    bind = eldap.bind(result_data[0][0], password)
                except Exception as auth_fail:
                    bind = auth_fail
                print(bind)
            print('groups:\n\n')
            groups = eldap.get_groups(result_data)
            print(groups)
            # testing for djbeca
            luser = result_data[0][1]
            print('username={0}'.format(luser['cn'][0]))
            print('email={0}'.format(luser['mail'][0]))
            print('first_name={0}'.format(luser['givenName'][0]))
            print('last_name={0}'.format(luser['sn'][0]))
            print('vitals:\n\n')
            phile = os.path.join('/d2/python_venv/3.6/djimix/djimix/sql/vitals.sql')
            with open(phile) as incantation:
                sql = incantation.read()
                sql = sql.replace('{CID}', str(cid))
            with get_connection() as connection:
                vitals = xsql(sql, connection).fetchone()
            print(vitals)
    else:
        print("El Dap fail")


if __name__ == '__main__':

    args = parser.parse_args()
    username = args.username
    password = args.password
    test = args.test
    sys.exit(main())
