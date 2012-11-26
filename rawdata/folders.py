# Python
from datetime import datetime, timedelta
from operator import itemgetter

# Django
from django.db.models import Q

class BaseFolderFactory(object):
    def __init__(self, source = [], *args, **kwargs):
        self.source = source

    def filter(self, params):
        filter_type = params.get('type')
        if filter_type:
            self.source = self.source.filter(image_type = filter_type)

        filter_upload = params.get('upload')
        if filter_upload:
            self.source = self.source.filter(
                Q(uploaded__gte = datetime.strptime(filter_upload, '%Y-%m-%d')) &
                Q(uploaded__lte = datetime.strptime(filter_upload, '%Y-%m-%d') + timedelta(days=1)));


class TypeFolderFactory(BaseFolderFactory):
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
