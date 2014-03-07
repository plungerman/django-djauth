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
    dn cn=username,o=users
    [and]
    password
"""

parser = OptionParser(description=desc)
parser.add_option("-d", "--dn", help="LDAP dn", dest="dn")
parser.add_option("-p", "--password", help="Password", dest="password")

def main():
    """
    main method
    """

    # initialize the manager
    l = LDAPManager(
        #protocol=settings.LDAP_PROTOCOL_PWM,
        server=settings.LDAP_SERVER_PWM,
        #port=settings.LDAP_PORT_PWM,
        user=settings.LDAP_USER_PWM,
        password=settings.LDAP_PASS_PWM,
        #password=settings.LDAP_PASS,
        base=settings.LDAP_BASE_PWM
    )
    #l = LDAPManager()
    print "dn = %s " % dn
    print "password = %s" % password
    status = l.update_password( dn, password )
    print status

######################
# shell command line
######################

if __name__ == "__main__":
    (options, args) = parser.parse_args()
    dn = options.dn
    password = options.password

    if not dn or not password:
        print "You must provide a dn attribute and a password.\n"
        parser.print_help()
        exit(-1)
    else:
        sys.exit(main())
