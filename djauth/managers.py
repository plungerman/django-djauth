# -*- coding: utf-8 -*-

import datetime
import sys

import ldap
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User


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
        self.lid_attr = settings.LDAP_ID_ATTR
        self.ret = settings.LDAP_RETURN
        self.valid_attributes = settings.LDAP_VALID_ATTR
        try:
            self.eldap = ldap.initialize(
                '{0}://{1}:{2}'.format(protocol, server, port),
            )
        except ldap.LDAPError as init_error:
            raise Exception(init_error)
        # set LDAPv3 option
        self.eldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
        # set debug level
        self.eldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        # require server certificate but ignore it's validity.
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        try:
            # bind the admin user
            self.eldap.simple_bind_s(user, password)
        except ldap.LDAPError as bind_error:
            raise Exception(bind_error)

    def unbind(self):
        """Disconnect and free resources when done."""
        self.eldap.unbind_s()

    def bind(self, dn, password):
        """Attempt to bind to the LDAP server with user's DN and password."""
        return self.eldap.simple_bind_s(dn, password)

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
            uid = ldap_data[self.lid_attr][0]
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
            for group in groups:
                grup = Group.objects.get(name__iexact=group)
                if not user.groups.filter(name=grup).exists():
                    grup.user_set.add(user)

        return user

    def search(self, find, field=None, ret=None):
        """
        Search for an LDAP user.

        Takes as argument a value and a valid unique field from
        the schema (e.g. cn, mail).
        Returns None or a list with a tuple containing a dictionary.
        """
        if not field:
            field = self.lid_attr
        elif field not in self.valid_attributes:
            return None
        philter = '({0}={1})'.format(field, find)
        if not ret:
            ret = self.ret
        search_result = self.eldap.search_s(
            self.base,
            ldap.SCOPE_SUBTREE,
            philter,
            list(ret),
        )
        # decode byte (e.g. b'larry') to utf-8
        if search_result and sys.version_info.major > 2:
            for key, instance in search_result[0][1].items():
                search_result[0][1][key][0] = instance[0].decode(encoding='utf-8')
        return search_result
