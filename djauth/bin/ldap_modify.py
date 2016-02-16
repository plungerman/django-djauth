# -*- coding: utf-8 -*-
"""
Shell script to search LDAP store by username or ID
"""

from django.conf import settings
from djauth.LDAPManager import LDAPManager

import sys
import hashlib, base64
import argparse
import ldap.modlist as modlist
import ldap

# set up command-line options
desc = """
Accepts as input:
    cn
    name [of attribute]
    value [of attribute]
"""

parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "-c", "--cn",
    required=True,
    help="LDAP cn",
    dest="cn"
)
parser.add_argument(
    "-n", "--name",
    required=True,
    help="Attribute name to modify",
    dest="name"
)
parser.add_argument(
    "-v", "--value",
    required=True,
    help="Attribute value to modify",
    dest="value"
)

def hash(password):
    return "{SHA}" + base64.encodestring(hashlib.sha1(str(password)).digest())

def main():
    """
    main method
    """

    global cn
    global name
    global value

    print "cn = {}".format(cn)
    print "name = {}".format(name)
    print "value = {}".format(value)

    # encrypt the password
    if name == "userPassword":
        value = hash(value)

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
    print search
    dn = search[0][0]
    print "dn = {}".format(dn)
    #result = l.modify(dn, name, value)
    old = {
        "dn":search[0][0],
        "cn":search[0][1]["cn"],
        "mail":search[0][1]["mail"],
        "carthageNameID":search[0][1]["carthageNameID"],
        "sn":search[0][1]["sn"],
        "carthageFormerStudentStatus":search[0][1]["carthageFormerStudentStatus"],
        "givenName":search[0][1]["givenName"],
        "carthageDob":search[0][1]["carthageDob"]
    }
    new = old
    new[name] = value
    #result = l.modify(dn, old, new)
    # success = (103, [])
    #print result

######################
# this doesn't really work for dn or cn but should work for other name/values
######################

if __name__ == "__main__":

    args = parser.parse_args()
    cn = args.cn
    name = args.name
    value = args.value

    print args

    if not cn or not name or not value:
        print "You must provide a cn, an attribute name, and an attribute value.\n"
        parser.print_help()
        exit(-1)
    else:
        sys.exit(main())

