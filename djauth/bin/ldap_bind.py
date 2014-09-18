from django.conf import settings
from django.contrib.auth.models import User, Group

from djauth.LDAPManager import LDAPManager

username = ""
password = ""

# initialise the LDAP manager
l = LDAPManager()

result_data = l.search(username,field="cn")

if not result_data:
    print result_data
    print "fail"
else:
    print result_data
    print "\n\n"
    print "dn = %s" % result_data[0][0]
    print "\n\n"
    print "Attempt to bind to the user's DN."
    print "\n\n"
    l.bind(result_data[0][0],password)
