# Python
from datetime import datetime, timedelta
from operator import itemgetter

# Django
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

class BaseFolderFactory(object):
    def __init__(self, *args, **kwargs):
        self.source = kwargs.pop('source', [])
        self.label = ''

    def get_label(self):
        return self.label

    def filter(self, params):
        filter_type = params.get('type')
        if filter_type:
            self.source = self.source.filter(image_type = filter_type)

        filter_upload = params.get('upload')
        if filter_upload:
            self.source = self.source.filter(
                Q(uploaded__gte = datetime.strptime(filter_upload, '%Y-%m-%d')) &
                Q(uploaded__lte = datetime.strptime(filter_upload, '%Y-%m-%d') + timedelta(days=1)));

        return self.source


class NoFolderFactory(BaseFolderFactory):
    """ A special kind of factory that produces no folders, useful if you
        still want to use .filter().
    """
    def __init__(self, *args, **kwargs):
        super(NoFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Name")

    def produce(self):
        return []


class TypeFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(TypeFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Type")

    def produce(self):
        from .templatetags.rawdata_tags import humanize_rawimage_type
        folders = [] # {'type': 123, 'label': 'abc', 'images': []}
        for image in self.source:
            t = image.image_type
            try:
                index = map(itemgetter('type'), folders).index(t)
                folders[index]['images'].append(image)
            except ValueError:
                folders.append({
                    'folder_type': 'type',
                    'type': t,
                    'label': humanize_rawimage_type(t),
                    'images': [image],
                });

        return folders


class UploadDateFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(UploadDateFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Upload date")

    def produce(self):
        folders = [] # {'date': _, 'label': _, 'images': []}
        for image in self.source:
            date = image.uploaded.date()
            try:
                index = map(itemgetter('date'), folders).index(date)
                folders[index]['images'].append(image)
            except ValueError:
                folders.append({
                    'folder_type': 'upload',
                    'date': date,
                    'label': date,
                    'images': [image],
                });

        return folders


FOLDER_TYPE_LOOKUP = {
    'none': NoFolderFactory,
    'type': TypeFolderFactory,
    'upload': UploadDateFolderFactory,
}


