from django.conf import settings
from django.contrib.auth.models import User, Group

from djauth.LDAPManager import LDAPManager


class LDAPBackend(object):
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        if not password:
            return None

        username = username.lower()
        # works for username and username@domain.com
        username = username.lower().split('@')[0]

        try:
            # initialise the LDAP manager
            l = LDAPManager()

            result_data = l.search(username,field="cn")
            # If the user does not exist in LDAP, Fail.
            if not result_data:
                return None
            # Attempt to bind to the user's DN.
            l.bind(result_data[0][0],password)
            # Success. The user existed and authenticated.
            # Get group
            group = None
            if result_data[0][1].get("carthageFacultyStatus"):
                if result_data[0][1]["carthageFacultyStatus"][0] == "A":
                    group = "carthageFacultyStatus"

            if result_data[0][1].get("carthageStaffStatus"):
                if result_data[0][1]["carthageStaffStatus"][0] == "A":
                    group = "carthageStaffStatus"

            if result_data[0][1].get("carthageStudentStatus"):
                if result_data[0][1]["carthageStudentStatus"][0] == "A":
                    group = "carthageStudentStatus"

            # Get the user record or create one with no privileges.
            try:
                user = User.objects.get(username__exact=username)
                if not user.last_name:
                    user.last_name = result_data[0][1]['sn'][0]
                    user.first_name = result_data[0][1]['givenName'][0]
                    user.save()
                try:
                    if group:
                        # add them to their group
                        # or 'except' if they already belong
                        g = Group.objects.get(name__iexact=group)
                        g.user_set.add(user)
                except:
                    return user
            except:
                # Create a User object.
                user = l.dj_create(
                    result_data, auth_user_pk=settings.LDAP_AUTH_USER_PK
                )

            # Success.
            return user

        except Exception as e:
            # Name or password were bad. Fail permanently.
            return None

    def get_user(self, user_id):
        """
        OJO: needed for django auth, don't delete
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
