import six
from django.utils.encoding import force_bytes
from django_redis.serializers.pickle import PickleSerializer

try:
    import cPickle as pickle
except ImportError:
    import pickle


class CustomPickleSerializer(PickleSerializer):

    def loads(self, value):
        if six.PY3:
            return self._loads_py3(value)
        return super().loads(force_bytes(value))

    def _loads_py3(self, value):
        return pickle.loads(
            force_bytes(value),
            fix_imports=True,
            encoding='latin1'
        )
