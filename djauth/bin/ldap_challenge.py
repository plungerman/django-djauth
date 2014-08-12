# -*- coding: utf-8 -*-
"""
Shell script to search LDAP store by username or ID
"""

from django.conf import settings
from djauth.LDAPManager import LDAPManager

from optparse import OptionParser
import os, sys, ldap

# set up command-line options
desc = """
Accepts as input:
    username
    [or]
    college ID
"""

parser = OptionParser(description=desc)
parser.add_option("-u", "--username", help="LDAP cn", dest="username")
parser.add_option("-i", "--id", help="College ID", dest="cid")

def main():
    """
    main method
    """

    # initialize the manager
    l = LDAPManager(
        protocol=settings.LDAP_PROTOCOL_PWM,
        server=settings.LDAP_SERVER_PWM,
        port=settings.LDAP_PORT_PWM,
        user=settings.LDAP_USER_PWM,
        password=settings.LDAP_PASS_PWM,
        base=settings.LDAP_BASE_PWM
    )

    if cid:
        field = settings.LDAP_ID_ATTR
        value = cid
    if username:
        field = "cn"
        value = username

    result = l.search(value,field=field,ret=settings.LDAP_RETURN_PWM)

    try:
        question = result[0][1][settings.LDAP_CHALLENGE_ATTR][0]
    except:
        question = None

    print question

######################
# shell command line
######################

if __name__ == "__main__":
    (options, args) = parser.parse_args()
    cid = options.cid
    username = options.username

    if not cid and not username:
        print "You must provide username or college ID.\n"
        parser.print_help()
        exit(-1)
    else:
        sys.exit(main())
