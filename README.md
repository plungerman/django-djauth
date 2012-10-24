DJ Auth
======

Django external authentication with LDAP. Built around Novell directory server, but should work for any LDAP.

Example Settings
================

Put in your settings.py file:

<pre><code>
LDAP_SERVER = "ldap.example.com"
LDAP_PORT = "636"
LDAP_PROTOCOL = "ldaps"
LDAP_BASE = "o=COMPANY"
LDAP_USER = "cn=ldapuser, o=COMPANY"
LDAP_PASS = "superstrongpassword"
LDAP_EMAIL_DOMAIN = "example.com"

AUTHENTICATION_BACKENDS = (
    'djauth.ldapBackend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)
</code></pre>

If LDAP auth fails, the system will fall back to Django authentication, which is good for system users like admin.
