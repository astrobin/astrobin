from abc import abstractmethod, ABCMeta


class AbstractPlateSolvingBackend(object, metaclass=ABCMeta):
    @abstractmethod
    def start(image, **kwargs):
        pass

