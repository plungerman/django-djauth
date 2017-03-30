# -*- coding: utf-8 -*-
"""
Shell script to delete LDAP user
"""

import django, os, sys

# env
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/usr/local/lib/python2.7/')
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/data2/django_trunk/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')

django.setup()

# now we can import settings
from django.conf import settings

from djauth.LDAPManager import LDAPManager

import argparse

# set up command-line options
desc = """
Accepts as input:
    college ID
"""


parser = argparse.ArgumentParser(description=desc)

parser.add_argument(
    "-i",
    "--cid",
    help="college ID",
    dest="cid",
    required=True
)

def main():
    """
    main method
    """


    # initialize the manager
    l = LDAPManager()
    result = l.search(cid, field='carthageNameID')
    print result[0][1]
    destroy = l.delete(result[0][1])

######################
# shell command line
######################

if __name__ == "__main__":
    args = parser.parse_args()
    cid = args.cid
    sys.exit(main())

