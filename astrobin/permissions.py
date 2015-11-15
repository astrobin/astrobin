from pybb.permissions import DefaultPermissionHandler

class PyBBMPermissions(DefaultPermissionHandler):
    # Disable forum polls
    def may_create_poll(self, user):
        return False
