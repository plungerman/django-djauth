# -*- coding: utf-8 -*-

import datetime
import sys

import ldap
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from ldap import modlist


class LDAPManager(object):
    """LDAP authentication manager and new user creator."""

    def __init__(
        self,
        protocol=settings.LDAP_PROTOCOL,
        server=settings.LDAP_SERVER,
        port=settings.LDAP_PORT,
        user=settings.LDAP_USER,
        password=settings.LDAP_PASS,
        base=settings.LDAP_BASE,
    ):
        """Initialise our class with the LDAP parameters for connection."""
        self.base = base
        try:
            self.eldap = ldap.initialize(
                '{0}://{1}:{2}'.format(protocol, server, port),
            )
        except ldap.LDAPError as error:
            raise Exception(error)
        # set LDAPv3 option
        self.eldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
        # set debug level
        self.eldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        # require server certificate but ignore it's validity.
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        try:
            # bind the admin user
            self.eldap.simple_bind_s(user, password)
        except ldap.LDAPError as error:
            raise Exception(error)

    def unbind(self):
        """Disconnect and free resources when done."""
        self.eldap.unbind_s()

    def bind(self, dn, password):
        """Attempt to bind to the LDAP server with user's DN and password."""
        return self.eldap.simple_bind_s(dn, password)

    def create(self, person):
        """
        Creates a new LDAP user.

        Takes as argument a dictionary with the following key/value pairs:

        objectclass                 ['User','etc']
        givenName                   [first name]
        sn                          [last name]
        carthageDob                 [date of birth]
        settings.LDAP_ID_ATTR       [college ID]
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

        dn = 'cn={0},{1}'.format(person['cn'], self.base)
        self.eldap.add_s(dn, user)
        return self.search(person[settings.LDAP_ID_ATTR])

    def dj_create(self, ldap_results, auth_user_pk=False, groups=None):
        """
        Create a Django User object for LDAP users.

        We obtain permissions, however we don't want them to be able
        to login without going through LDAP with this user. So we
        effectively disable their non-LDAP login ability by
        setting it to a random password that is not given to
        them. In this way, static users that don't go through
        ldap can still login properly, and LDAP users still
        have a User object.
        """
        now = datetime.datetime.now()
        ldap_data = ldap_results[0][1]
        email = ldap_data['mail'][0]
        # if auth_user_pk is True, then we use the primary key from
        # the database rather than the LDAP user ID
        if auth_user_pk:
            uid = None
        else:
            # this will barf 500 if we don't have an ID
            uid = ldap_data[settings.LDAP_ID_ATTR][0]
        cn = ldap_data['cn'][0]
        password = User.objects.make_random_password(length=32)
        user = User.objects.create(
            pk=uid, username=cn, email=email, last_login=now,
        )
        user.set_password(password)
        user.first_name = ldap_data['givenName'][0]
        user.last_name = ldap_data['sn'][0]
        user.save()
        # add to groups
        if groups:
            # onelogin
        else:
            # novell
            for key, _ in settings.LDAP_GROUPS.items():
                group = ldap_data.get(key)
                if group and group[0] == 'A':
                    grup = Group.objects.get(name__iexact=key)
                    grup.user_set.add(user)
        return user

    def update_password(self, dn, password):
        """
        Change an LDAP user's password.

        Takes a dn and a password.

        The passwd_s() method and its asynchronous counterpart, passwd()
        take three arguments:

        The DN of the record to change.
        The old password (or None if an admin user makes the change)
        The new password

        If the passwd_s change is successful, it returns a tuple with the
        status code (ldap.RES_EXTENDED, which is the integer 120), and an
        empty list:

        (120, [])

        passwd returns a result ID code.

        Novell do not seem to support 3062 so passwd & passwd_s fail
        with a PROTOCOL_ERROR. Returns 2 if using passwd, which means
        the same thing.
        """
        # print("protocol version = %s" % self.eldap.protocol_version)
        # print(ldap.TLS_AVAIL)
        # print("require cert = {}".format(ldap.OPT_X_TLS_REQUIRE_CERT))
        status = self.eldap.passwd_s(dn, None, password)

        return status

    def modify_list(self, dn, old, new):
        """Modifie an LDAP user's attribute."""
        # print("old = {}".format(old))
        # print("new = {}".format(new))
        ldif = modlist.modifyModlist(old, new)
        # print("modlist = {}".format(ldif))
        # Do the actual modification
        return self.eldap.modify_s(dn, ldif)

    def modify(self, dn, name, attr_val):
        """Modifie an LDAP user's attribute."""
        # ldif = modlist.modifyModlist(old,new)
        # Do the actual modification
        # self.eldap.modify_s(dn,ldif)
        return self.eldap.modify_s(dn, [(ldap.MOD_REPLACE, name, str(att_val))])

    def delete(self, person):
        """
        Delete an LDAP user.

        Takes as argument a dictionary with the following key/value pairs:

        cn              [username]
        """
        dn = 'cn={0},{1}'.format(person['cn'][0], self.base)
        # print(dn)

        try:
            self.eldap.delete_s(dn)
        except ldap.LDAPError as error:
            raise Exception(error)

    def search(
            self,
            find,
            field=settings.LDAP_ID_ATTR,
            philter=None,
            ret=settings.LDAP_RETURN,
        ):
        """
        Search for an LDAP user.

        Takes as argument a value and a valid unique field from
        the schema (i.e. LDAP_ID_ATTR, cn, mail).
        Returns None or a list with a tuple containing a dictionary.
        """
        valid = ['cn', settings.LDAP_ID_ATTR, 'mail']
        if field not in valid:
            return None
        if not philter:
            philter = '(&(objectclass={0}) ({1}={2}))'.format(
                settings.LDAP_OBJECT_CLASS, field, find,
            )

        search_result = self.eldap.search_s(
            self.base,
            ldap.SCOPE_SUBTREE,
            philter,
            [x for x in ret],
        )
        # decode byte (e.g. b'larry') to utf-8
        if search_result and sys.version_info.major > 2:
            for n, v in search_result[0][1].items():
                search_result[0][1][n][0] = v[0].decode(encoding='utf-8')
        return search_result
