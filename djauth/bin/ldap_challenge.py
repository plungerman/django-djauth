# -*- coding: utf-8 -*-
"""
Shell script to search LDAP store by username or ID
"""

from optparse import OptionParser

import os, sys, ldap

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
        server=settings.LDAP_SERVER_PWM,
        user=settings.LDAP_USER_PWM,
        password=settings.LDAP_PASS_PWM
    )

    if cid:
        field = settings.LDAP_ID_ATTR
        value = cid
    if username:
        field = "cn"
        value = username

    result = l.search(value,field=field,ret=settings.LDAP_RETURN_PWM)

    try:
        question = result[0][1]['pwmResponseSet'][0]
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
