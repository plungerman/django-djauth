# -*- coding: utf-8 -*-
"""
Shell script to search LDAP store by username or ID
"""

from django.conf import settings
from djauth.LDAPManager import LDAPManager

from optparse import OptionParser
import os, sys, ldap
import hashlib, base64

# set up command-line options
desc = """
Accepts as input:
    cn
    name [of attribute]
    value [of attribute]
"""

parser = OptionParser(description=desc)
parser.add_option("-c", "--cn", help="LDAP cn", dest="cn")
parser.add_option("-n", "--name", help="Attribute name to modify", dest="name")
parser.add_option("-v", "--value", help="Attribute value to modify", dest="value")

def hash(password):
    return "{SHA}" + base64.encodestring(hashlib.sha1(str(password)).digest())

def main():
    """
    main method
    """
    print cn
    print name
    print value

    # encrypt the password
    #if name == "userPassword":
    #    value = hash(value)

    # initialize the manager
    if name == "userPassword":
        l = LDAPManager(
            protocol=settings.LDAP_PROTOCOL_PWM,
            server=settings.LDAP_SERVER_PWM,
            port=settings.LDAP_PORT_PWM,
            user=settings.LDAP_USER_PWM,
            password=settings.LDAP_PASS_PWM,
            base=settings.LDAP_BASE_PWM
        )
    else:
        l = LDAPManager()
    # use search to obtain dn
    search = l.search(cn,field="cn")
    dn = search[0][0]
    result = l.modify(dn, name, value)

    # success = (103, [])
    print result

######################
# shell command line
######################

if __name__ == "__main__":
    (options, args) = parser.parse_args()
    cn = options.cn
    name = options.name
    value = options.value

    if not cn or not name or not value:
        print "You must provide a cn, an attribute name, and an attribute value.\n"
        parser.print_help()
        exit(-1)
    else:
        sys.exit(main())
