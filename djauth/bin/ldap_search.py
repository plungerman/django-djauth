# -*- coding: utf-8 -*-
"""
Shell script to search LDAP store by username or ID
"""

from optparse import OptionParser

import os, sys

# env
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/usr/local/lib/python2.7/')
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/data2/django_trunk/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djaludir.settings")

# now we can import settings
from django.conf import settings

from djauth.LDAPManager import LDAPManager

# set up command-line options
desc = """
Accepts as input:
    attribute value
    attribute name

Valid attributes:
    ["cn","carthageNameID","mail"]
"""

parser = OptionParser(description=desc)
parser.add_option("-f", "--att_name", help="Schema attribute field name.", dest="field")
parser.add_option("-v", "--att_val", help="Schema attribute value.", dest="value")
parser.add_option("-p", "--password", help="Person's password.", dest="password")

def main():
    """
    main method
    """

    # initialize the manager
    l = LDAPManager()

    result = l.search(value,field=field)
    print result

    # authenticate
    if password:
        l.bind(result[0][0],password)

######################
# shell command line
######################

if __name__ == "__main__":
    (options, args) = parser.parse_args()
    field = options.field
    value = options.value
    password = options.password

    valid = ["cn","carthageNameID","mail"]
    if not field and not value:
        print "You must provide an attribute name and its value.\n"
        parser.print_help()
        exit(-1)
    elif field not in valid:
        print "Your attribute is not valid.\n"
        parser.print_help()
        exit(-1)
    else:
        sys.exit(main())

