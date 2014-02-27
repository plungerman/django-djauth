#!/usr/bin/env python
#
# A short script to print DN information about a SASL user.
# from:
# http://www.packtpub.com/article/installing-and-configuring-the-python-ldap-library-and-binding-to-an-ldap-directory

import ldap, ldap.sasl
import sys, getpass

user_name = None
pw = None

usage="""%s [username]

Log in as a SASL user and get the user's DN.

If a username is specified, this will be used as the SASL ID.
Otherwise,the username will be retrieved from the
environment.""" % sys.argv[0]

if len(sys.argv) > 1:
    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print usage
        sys.exit()
    user_name = sys.argv[1]
else:
    user_name = getpass.getuser()

pw = getpass.getpass("Password for %s: " % user_name)

try:
    con = ldap.initialize("%s://%s" % (settings.LDAP_PROTOCOL,settings.LDAP_SERVER)
    auth_tokens = ldap.sasl.digest_md5( user_name, pw )

    try:
        con.sasl_interactive_bind_s( "", auth_tokens )
        sys.stdout.write(con.whoami_s())
        sys.stdout.write("n")
    except ldap.LDAPError, e:
        sys.stderr.write("Fatal Error.n")
        if type(e.message) == dict:
            for (k, v) in e.message.iteritems():
                sys.stderr.write("%s: %sn" % (k, v))
        else:
            sys.stderr.write("Error: %sn" % e.message);

        sys.exit()
finally:
    try:
        con.unbind()
    except ldap.LDAPError, e:
        pass
