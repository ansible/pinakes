"""User Capabilities"""
import logging

logger = logging.getLogger("catalog")


class UserCapabilities:
    """Collect User Capabilities based on permission sets
    defined in a dict
    """

    capabilities_map = {}

    def __init__(self, user, obj):
        self.user = user
        self.obj = obj

    def get(self):
        """Get the user capabilties for the specified object"""
        kwargs = {
            "app_label": self.obj.__class__._meta.app_label,
            "model_name": self.obj.__class__._meta.model_name,
        }
        assigned_permissions = self.user.get_all_permissions(self.obj)
        capabilities = {}
        status = {}
        for key, required_perms in self.capabilities_map.items():
            for perm in required_perms:
                if perm in status:
                    result = status[perm]
                else:
                    status[perm] = perm % kwargs in assigned_permissions
                    result = status[perm]

                if not result:
                    capabilities[key] = False
                    break

                capabilities[key] = True
        return capabilities


class PortfolioUserCapabilities(UserCapabilities):
    """User capabilities for Portfolio objects"""

    capabilities_map = {
        "create": ["%(app_label)s.add_%(model_name)s"],
        "update": ["%(app_label)s.change_%(model_name)s"],
        "destroy": ["%(app_label)s.delete_%(model_name)s"],
        "copy": [
            "%(app_label)s.view_%(model_name)s",
            "%(app_label)s.add_%(model_name)s",
        ],
        "share": ["%(app_label)s.change_%(model_name)s"],
        "unshare": ["%(app_label)s.change_%(model_name)s"],
        "show": ["%(app_label)s.view_%(model_name)s"],
        "set_approval": ["%(app_label)s.change_%(model_name)s"],
        "tag": ["%(app_label)s.change_%(model_name)s"],
        "untag": ["%(app_label)s.change_%(model_name)s"],
    }


class PortfolioItemUserCapabilities(UserCapabilities):
    """User capabilities for PortfolioItem objects"""

    capabilities_map = {
        "create": ["%(app_label)s.change_%(model_name)s"],
        "update": ["%(app_label)s.change_%(model_name)s"],
        "destroy": ["%(app_label)s.change_%(model_name)s"],
        "copy": [
            "%(app_label)s.view_%(model_name)s",
            "%(app_label)s.change_%(model_name)s",
        ],
        "show": ["%(app_label)s.view_%(model_name)s"],
        "set_approval": ["%(app_label)s.change_%(model_name)s"],
        "edit_survey": ["%(app_label)s.change_%(model_name)s"],
        "tag": ["%(app_label)s.change_%(model_name)s"],
        "untag": ["%(app_label)s.change_%(model_name)s"],
    }
