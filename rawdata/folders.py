class BaseFolder(object):
    """ A base folder that has simple methods to handle the image
        collection.
    """
    def __init__(self, *args, **kwargs):
        self.label = kwargs.pop('label', '')
        self.images = [] 
    
    def get_images(self):
        return self.images

    def add_image(self, image):
        self.images.append(image)

    def get_label(self):
        return self.label


class TypeFolder(BaseFolder):
    """ A folder that holds images by type. Types are defined in the
        RawImage model.
    """
    def __init__(self, *args, **kwargs):
        super(TypeFolder, self).__init__(*args, **kwargs)
        self.type_ = kwargs.pop('type', 0)
        self.source = kwargs.pop('source', [])

    def get_type(self):
        return self.type_

    def populate(self):
        for image in self.source:
            if image.image_type == self.type_:
                self.add_image(image)

