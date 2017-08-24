# -*- coding: utf-8 -*-
"""
Shell script to search LDAP store by username or ID
"""

import django, os, sys

# env
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/usr/local/lib/python2.7/')
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/data2/django_1.11/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')

django.setup()

# now we can import settings
from django.conf import settings

from djauth.LDAPManager import LDAPManager

import argparse

# set up command-line options
desc = """
Accepts as input:\n\r
    attribute value
    attribute name

Valid attributes:
    ["cn","carthageNameID","mail","carthageDob"]

returns one tuple or a list of tuples in the following format:

(
    'cn=av,ou=users,o=carthage', {
        'cn': ['av'], 'carthageNameID': ['999998'], 'sn': ['V'],
        'mail': ['av@carthage.edu'], 'givenName': ['Audio'],
        'carthageDob': ['1999-09-09']
    }
)
"""

parser = argparse.ArgumentParser(
    description=desc, formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument(
    "-f", "--att_name",
    dest='field',
    required=True,
    help="Schema attribute field name."
)
parser.add_argument(
    "-v", "--att_val",
    dest='value',
    required=True,
    help="Schema attribute value."
)
parser.add_argument(
    "-p", "--password",
    dest='password',
    help="Person's password."
)
parser.add_argument(
    "-c", "--create",
    dest='create',
    help="Create a Django account."
)


def main():
    """
    main method
    """

    # initialize the manager
    l = LDAPManager()
    """
    l = LDAPManager(
        protocol=settings.LDAP_PROTOCOL_PWM,
        server=settings.LDAP_SERVER_PWM,
        port=settings.LDAP_PORT_PWM,
        user=settings.LDAP_USER_PWM,
        password=settings.LDAP_PASS_PWM,
        base=settings.LDAP_BASE_PWM
    )
    """
    result = l.search(value,field=field)

    if field == 'carthageDob':
        for r in result:
            p = "{cn[0]}|{carthageNameID[0]}|{sn[0]}|{givenName[0]}|{mail[0]}"
            print p.format(**r[1])
    else:
        print result

    # authenticate
    if password:
        auth = l.bind(result[0][0],password)
        print auth
        # create a django user
        if create:
            user = l.dj_create(result[0][1]['cn'][0],result)
            print user

######################
# shell command line
######################

if __name__ == '__main__':

    args = parser.parse_args()
    field = args.field
    value = args.value
    password = args.password
    create = args.create

    valid = ['cn','carthageNameID','mail','carthageDob']

    if field not in valid:
        print "Your attribute is not valid.\n"
        exit(-1)
    else:
        sys.exit(main())
