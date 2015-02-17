from django.conf import settings

from djzbar.utils.informix import do_sql
from directory.core import FACSTAFF_ALPHA

import ldap

facStaffList=[]

facStaffQuery = do_sql(FACSTAFF_ALPHA)
for x in facStaffQuery:
       facStaffList.append(x.id)

facstaff_no_questions=0;

facstaffFilter = ''
for ID in facStaffList:
    facstaffFilter += "({}={})".format(
        settings.LDAP_ID_ATTR,str(ID)
    )

status='Success'
base = settings.LDAP_BASE
scope = ldap.SCOPE_SUBTREE
filter = "(&(objectclass=person)(|{}))".format(facstaffFilter)
ret = settings.LDAP_RETURN_PWM

try:
    l = ldap.initialize('{}://{}:{}'.format(
            settings.LDAP_PROTOCOL_PWM,
            settings.LDAP_SERVER_PWM,
            settings.LDAP_PORT_PWM
        )
    )
    l.protocol_version = ldap.VERSION3
    l.simple_bind_s(
        settings.LDAP_USER_PWM,settings.LDAP_PASS_PWM
    )
except ldap.LDAPError:
    status='Failed'

results = l.search_s(base, scope, filter, ret)
for r in results:
    try:
        if r[1]['pwmResponseSet']:
            status='FAIL'
    except KeyError:
        facstaff_no_questions=facstaff_no_questions+1

print facstaff_no_questions
