# Python
from datetime import datetime, timedelta
from operator import itemgetter

# Django
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

UNKNOWN_LABEL = "---------"

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
                Q(uploaded__lte = datetime.strptime(filter_upload, '%Y-%m-%d') + timedelta(days=1)))

        filter_acquisition = params.get('acquisition')
        if filter_acquisition:
            self.source = self.source\
                .filter(
                    Q(acquisition_date__gte = datetime.strptime(filter_acquisition, '%Y-%m-%d')) &
                    Q(acquisition_date__lte = datetime.strptime(filter_acquisition, '%Y-%m-%d') +
                                              timedelta(days=1)))

        filter_camera = params.get('camera')
        if filter_camera:
            if filter_camera != UNKNOWN_LABEL:
                self.source = self.source.filter(camera = filter_camera)
            else:
                self.source = self.source.filter(camera__isnull = True)

        filter_telescope = params.get('telescope')
        if filter_telescope:
            if filter_telescope != UNKNOWN_LABEL:
                self.source = self.source.filter(telescopeName = filter_telescope)
            else:
                self.source = self.source.filter(telescopeName__isnull = True)

        filter_filter = params.get('filter')
        if filter_filter:
            if filter_filter != UNKNOWN_LABEL:
                self.source = self.source.filter(filterName = filter_filter)
            else:
                self.source = self.source.filter(filterName__isnull = True)

        filter_subject = params.get('subject')
        if filter_subject:
            if filter_subject != UNKNOWN_LABEL:
                self.source = self.source.filter(subjectName = filter_subject)
            else:
                self.source = self.source.filter(subjectName__isnull = True)

        filter_temperature = params.get('temperature')
        if filter_temperature:
            if filter_temperature != UNKNOWN_LABEL:
                self.source = self.source.filter(temperature = filter_temperature)
            else:
                self.source = self.source.filter(temperature__isnull = True)

        return self.source


class NoFolderFactory(BaseFolderFactory):
    """ A special kind of factory that produces no folders, useful if you
        still want to use .filter().
    """
    def __init__(self, *args, **kwargs):
        super(NoFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Name")
        self.source = self.source.order_by('-pk')

    def produce(self):
        return []


class TypeFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(TypeFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Type")
        self.source = self.source.order_by('-image_type')

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
                })

        return folders


class UploadDateFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(UploadDateFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Upload date")
        self.source = self.source.order_by('-uploaded')

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
                })

        return folders


class AcquisitionDateFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(AcquisitionDateFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Acquisition date")
        self.source = self.source.order_by('-acquisition_date')

    def produce(self):
        folders = [] # {'date': _, 'label': _, 'images': []}
        for image in self.source:
            if image.acquisition_date:
                date = image.acquisition_date.date()
                try:
                    index = map(itemgetter('date'), folders).index(date)
                    folders[index]['images'].append(image)
                except ValueError:
                    folders.append({
                        'folder_type': 'acquisition',
                        'date': date,
                        'label': date,
                        'images': [image],
                    })

        return folders


class CameraFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(CameraFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Camera")
        self.source = self.source.order_by('camera')

    def produce(self):
        folders = [] # {'camera': 'abc', 'label': 'abc', 'images': []}
        for image in self.source:
            camera = image.camera if image.camera else UNKNOWN_LABEL 
            try:
                index = map(itemgetter('camera'), folders).index(camera)
                folders[index]['images'].append(image)
            except ValueError:
                folders.append({
                    'folder_type': 'camera',
                    'camera': camera,
                    'label': camera,
                    'images': [image],
                })

        return folders


class TelescopeFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(TelescopeFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Telescope or lens")
        self.source = self.source.order_by('telescopeName')

    def produce(self):
        folders = [] # {'telescope': 'abc', 'label': 'abc', 'images': []}
        for image in self.source:
            telescope = image.telescopeName if image.telescopeName else UNKNOWN_LABEL 
            try:
                index = map(itemgetter('telescope'), folders).index(telescope)
                folders[index]['images'].append(image)
            except ValueError:
                folders.append({
                    'folder_type': 'telescope',
                    'telescope': telescope,
                    'label': telescope,
                    'images': [image],
                })

        return folders


class FilterFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(FilterFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Filter")
        self.source = self.source.order_by('filterName')

    def produce(self):
        folders = [] # {'filter': 'abc', 'label': 'abc', 'images': []}
        for image in self.source:
            filterName = image.filterName if image.filterName else UNKNOWN_LABEL 
            try:
                index = map(itemgetter('filterName'), folders).index(filterName)
                folders[index]['images'].append(image)
            except ValueError:
                folders.append({
                    'folder_type': 'filterName',
                    'filterName': filterName,
                    'label': filterName,
                    'images': [image],
                })

        return folders


class SubjectFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(SubjectFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Subject")
        self.source = self.source.order_by('subjectName')

    def produce(self):
        folders = [] # {'subject': 'abc', 'label': 'abc', 'images': []}
        for image in self.source:
            subjectName = image.subjectName if image.subjectName else UNKNOWN_LABEL 
            try:
                index = map(itemgetter('subjectName'), folders).index(subjectName)
                folders[index]['images'].append(image)
            except ValueError:
                folders.append({
                    'folder_type': 'subjectName',
                    'subjectName': subjectName,
                    'label': subjectName,
                    'images': [image],
                })

        return folders


class TemperatureFolderFactory(BaseFolderFactory):
    def __init__(self, *args, **kwargs):
        super(TemperatureFolderFactory, self).__init__(*args, **kwargs)
        self.label = _("Temperature")
        self.source = self.source.order_by('-temperature')

    def produce(self):
        folders = [] # {'temperature': '123', 'label': '123', 'images': []}
        for image in self.source:
            temperature = image.temperature if image.camera else UNKNOWN_LABEL 
            try:
                index = map(itemgetter('temperature'), folders).index(temperature)
                folders[index]['images'].append(image)
            except ValueError:
                folders.append({
                    'folder_type': 'temperature',
                    'temperature': temperature,
                    'label': temperature,
                    'images': [image],
                })

        return folders


FOLDER_TYPE_LOOKUP = {
    'none': NoFolderFactory,
    'type': TypeFolderFactory,
    'upload': UploadDateFolderFactory,
    'acquisition': AcquisitionDateFolderFactory,
    'camera': CameraFolderFactory,
    'telescope': TelescopeFolderFactory,
    'filter': FilterFolderFactory,
    'subject': SubjectFolderFactory,
    'temperature': TemperatureFolderFactory,
}

