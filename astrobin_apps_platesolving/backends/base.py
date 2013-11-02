from abc import ABCMeta, abstractmethod

class AbstractPlateSolvingBackend(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def start(image):
        pass

