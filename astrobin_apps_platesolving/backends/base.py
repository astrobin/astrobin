from abc import abstractmethod, ABCMeta


class AbstractPlateSolvingBackend(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def start(image, **kwargs):
        pass

