from rest_framework import permissions


class IsImageOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        klass = obj.__class__.__name__
        if klass == u'Image':
            return obj.user == request.user
        elif klass == u'ImageRevision' or klass == u'UncompressedSourceUpload':
            return obj.image.user == request.user

        raise ValueError("obj must be an Image or an ImageRevision")
