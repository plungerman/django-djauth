#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse

import django
import sys


django.setup()


from djauth.LDAPManager import LDAPManager


# set up command-line options
desc = """
Accepts as input:\n\r
    attribute value
    attribute name

Valid attributes:
    "cn", "carthageNameID", "mail", "sn"

returns a list of tuples.
"""

parser = argparse.ArgumentParser(
    description=desc, formatter_class=argparse.RawTextHelpFormatter,
)

parser.add_argument(
    "-f",
    "--att_name",
    dest='field',
    required=True,
    help="Schema attribute field name.",
)
parser.add_argument(
    "-v",
    "--att_val",
    dest='value',
    required=True,
    help="Schema attribute value.",
)
parser.add_argument(
    "-p",
    "--password",
    dest='password',
    help="Person's password.",
)
parser.add_argument(
    "-c",
    "--create",
    dest='create',
    help="Create a Django account.",
)


def main():
    """Search LDAP store by username, ID, or email."""
    # initialize the manager
    eldap = LDAPManager()
    result_data = eldap.search(value, field=field)
    print(result_data)

    # authenticate
    if password and field == 'cn':
        auth = l.bind(result_data[0][0], password)
        print(auth)
        # create a django user
        if create:
            user = l.dj_create(result_data[0][1]['cn'][0], result_data)
            print(user)


if __name__ == '__main__':

    args = parser.parse_args()
    field = args.field
    value = args.value
    password = args.password
    create = args.create

    valid = ['cn', 'carthageNameID', 'mail', 'sn']

    if field not in valid:
        print("Your attribute is not valid.\n")
        exit(-1)
    else:
        sys.exit(main())
