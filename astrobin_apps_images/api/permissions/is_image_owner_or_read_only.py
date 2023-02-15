from rest_framework import permissions


class IsImageOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        klass = obj.__class__.__name__

        if klass == 'Image':
            return obj.user == request.user

        elif klass in ('ImageRevision', 'UncompressedSourceUpload', 'DeepSky_Acquisition', 'SolarSystem_Acquisition'):
            return obj.image.user == request.user

        raise ValueError(
            "obj must be one of: "
            "'Image', 'ImageRevision', 'UncompressedSourceUpload', 'DeepSky_Acquisition', 'SolarSystem_Acquisition'"
        )
