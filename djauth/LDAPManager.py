# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User, Group

import ldap
import ldap.modlist as modlist

import logging
logger = logging.getLogger(__name__)

class LDAPManager(object):

    def __init__(self,protocol=None,port=None,server=None,user=None,password=None):
        # Authenticate the base user so we can search
        if protocol is None:
            protocol = settings.LDAP_PROTOCOL
        if port is None:
            port = settings.LDAP_PORT
        if server is None:
            server = settings.LDAP_SERVER
        if user is None:
            user = settings.LDAP_USER
        if password is None:
            password = settings.LDAP_PASS
        try:
            self.l = ldap.initialize(
                '%s://%s:%s' % (protocol,server,port)
            )
            self.l.protocol_version = ldap.VERSION3
            self.l.simple_bind_s(user,password)
        except ldap.LDAPError, e:
            raise Exception(e)

    def unbind(self):
        #
        # Disconnect and free resources when done
        #
        self.l.unbind_s()

    def bind(self, dn, password):

        # Attempt to bind to the user's DN.
        # we need try/except here for edge cass errors
        # like server refuses to execute.
        try:
            self.l.simple_bind_s(dn,password)
        except ldap.LDAPError, e:
            raise Exception(e)

    def create(self, person):
        """
        Creates a new LDAP user.
        Takes as argument a dictionary with the following key/value pairs:

        objectclass                 ["User","etc"]
        givenName                   [first name]
        sn                          [last name]
        carthageDob                 [date of birth]
        carthageNameID              [college ID]
        cn                          [we use email for username]
        mail                        [email]
        userPassword                [password]
        carthageFacultyStatus       [faculty]
        carthageStaffStatus         [staff]
        carthageStudentStatus       [student]
        carthageFormerStudentStatus [alumni]
        carthageOtherStatus         [trustees etc]
        """
        user = modlist.addModlist(person)

        dn = 'cn=%s,%s' % (person["cn"],settings.LDAP_BASE)
        self.l.add_s(dn, user)
        return self.search(person["carthageNameID"])

    def dj_create(self, data):
        # We create a User object for LDAP users so we can get
        # permissions, however we -don't- want them to be able to
        # login without going through LDAP with this user. So we
        # effectively disable their non-LDAP login ability by
        # setting it to a random password that is not given to
        # them. In this way, static users that don't go through
        # ldap can still login properly, and LDAP users still
        # have a User object.

        data = data[0][1]
        email = data['mail'][0]
        uid = data['carthageNameID'][0]
        cn = data['cn'][0]
        password = User.objects.make_random_password(length=24)
        user = User.objects.create(pk=uid,username=cn,email=email)
        user.set_password(password)
        user.first_name = data['givenName'][0]
        user.last_name = data['sn'][0]
        user.save()
        # add to groups
        for key, val in settings.LDAP_GROUPS.items():
            group = data.get(key)
            if group and group[0] == 'A':
                g = Group.objects.get(name__iexact=key)
                g.user_set.add(user)
        return user

    def update(self, person):
        """
        Updates an LDAP user.
        """

        # Some place-holders for old and new values
        old = {'description':'User object for replication using slurpd'}
        new = {'description':'Bind object used for replication using slurpd'}

        # Convert place-holders for modify-operation using modlist-module
        ldif = modlist.modifyModlist(old,new)

        # Do the actual modification
        l.modify_s(dn,ldif)

    def delete(self, person):
        """
        Deletes an LDAP user.
        Takes as argument a dictionary with the following key/value pairs:

        cn              [username]
        """
        dn = "cn=%s,%s" % (person["cn"],settings.LDAP_BASE)
        try:
            self.l.delete_s(dn)
        except ldap.LDAPError, e:
            raise Exception(e)

    def search(self, val, field="carthageNameID"):
        """
        Searches for an LDAP user.
        Takes as argument a value and a valid unique field from
        the schema (i.e. carthageNameID, cn, mail).
        Returns a list with dn tuple and a dictionary with the
        following key/value pairs:

        givenName               [first name]
        sn                      [last name]
        cn                      [username]
        carthageDob             [date of birth]
        carthageNameID          [college ID]
        carthageStaffStatus     [staff?]
        carthageOtherStatus     [alumni?]
        carthageFacultyStatus   [faculty?]
        carthageStudentStatus   [student?]
        mail                    [email]
        """

        valid = ["cn","carthageNameID","mail"]
        if field not in valid:
            return None
        philter = "(&(objectclass=%s) (%s=%s))" % (
            settings.LDAP_OBJECT_CLASS,field,val
        )
        ret = settings.LDAP_RETURN

        result_id = self.l.search(
            settings.LDAP_BASE,ldap.SCOPE_SUBTREE,philter,ret
        )
        result_type, result_data = self.l.result(result_id, 0)
        # If the user does not exist in LDAP, Fail.
        if (len(result_data) != 1):
            return None
        else:
            return result_data
