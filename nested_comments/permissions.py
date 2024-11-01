from rest_framework import permissions


class IsCommentAuthorOrContentOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only the author of a comment or the content owner to delete it.
    Only the comment author can update it, and all users have read-only access.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow the author of the comment or the content owner to delete
        if request.method == 'DELETE':
            content_owner = getattr(obj.content_object, 'user', None)
            return obj.author == request.user or content_owner == request.user

        # Only the comment author can update the comment
        return obj.author == request.user
