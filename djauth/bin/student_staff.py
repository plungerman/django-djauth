# -*- coding: utf-8 -*-
import datetime
import django
import os
import sys
# env
sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/usr/lib/python2.7/')
sys.path.append('/usr/local/lib/python2.7/dist-packages/')
sys.path.append('/data2/django_1.9/')
sys.path.append('/data2/django_projects/')
sys.path.append('/data2/django_third/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djpsilobus.settings")

django.setup()

from djsani.core.sql import STUDENTS_ALPHA
from directory.core import STUDENTS_ALL
from djzbar.utils.informix import do_sql as do_esql
from djsani.core.utils import get_term
from djauth.LDAPManager import LDAPManager

from django.conf import settings

# set up command-line options

def main():
    """
    Find all students who have staff attribute in LDAP
    """

    NOW  = datetime.datetime.now()
    term = get_term()
    sql = ''' {}
        AND stu_serv_rec.yr = "{}"
        AND stu_serv_rec.sess = "{}"
        AND prog_enr_rec.cl IN {}
    '''.format(
        STUDENTS_ALPHA, term["yr"], term["sess"],
        ('FN','FF','FR','SO','JR','SR','GD','UT')
    )
    #print "djsani sql = {}".format(sql)
    #print "djkotter sql = {}".format(STUDENTS_ALL)
    #objs = do_esql(sql)
    objs = do_esql(STUDENTS_ALL)

    # initialize the LDAP manager
    l = LDAPManager()
    print NOW
    for o in objs:
        print "{}, {} ({})".format(o.lastname, o.firstname, o[2])
        result = l.search(o.id,field=settings.LDAP_ID_ATTR)
        staff = result[0][1].get('carthageStaffStatus')

        if staff:
            staff = staff[0]
            username = result[0][1]['cn'][0]
            email = result[0][1].get('mail')
            if email:
                email = email[0]
            print "username = {} | id {} | email = {} | staff = {}".format(
                username, o.id, email, staff
            )
    print NOW


######################
# shell command line
######################

if __name__ == "__main__":

    sys.exit(main())
