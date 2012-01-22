import string
import re
import datetime

from haystack.indexes import *
from haystack import site

from astrobin.models import Image
from astrobin.models import DeepSky_Acquisition
from astrobin.models import SolarSystem_Acquisition
from astrobin.models import Subject, SubjectIdentifier

from django.contrib.auth.models import User
from django.db.models import Q

from hitcount.models import HitCount

def xapian_escape(s):
    return ''.join(ch for ch in s if ch not in set(string.punctuation))

def _join_stripped(a):
    escaped = []
    for i in a:
        x = xapian_escape(''.join(i.split()))
        escaped.append(x)

    return a + escaped 

def _get_integration(image):
    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None
    integration = 0

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=image)
    except:
        pass

    if deep_sky_acquisitions:
        for a in deep_sky_acquisitions:
            if a.duration and a.number:
                integration += (a.duration * a.number)
    elif solar_system_acquisition:
        return 0

    return integration


class UserIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    user_name = CharField(model_attr='username')
    user_images = IntegerField()
    user_integration = IntegerField()
    user_avg_integration = IntegerField()

    def index_queryset(self):
        return User.objects.all()

    def get_model(self):
        return User

    def prepare_user_images(self, obj):
        return len(Image.objects.filter(user = obj))

    def prepare_user_integration(self, obj):
        integration = 0
        for i in Image.objects.filter(user = obj):
            integration += _get_integration(i)

        return integration / 3600.0

    def prepare_user_avg_integration(self, obj):
        integration = 0
        images = 0
        for i in Image.objects.filter(user = obj):
            image_integration = _get_integration(i)
            if image_integration:
                images += 1
                integration += image_integration

        return (integration / 3600.0) / images if images else 0

       
class ImageIndex(SearchIndex):
    text = CharField(document=True, use_template=True)

    title = CharField(model_attr='title')
    description = CharField(model_attr='description')
    uploaded = DateTimeField(model_attr='uploaded')

    username = CharField()
    subjects = MultiValueField()
    imaging_telescopes = MultiValueField()
    guiding_telescopes = MultiValueField()
    mounts = MultiValueField()
    imaging_cameras = MultiValueField()
    guiding_cameras = MultiValueField()
    focal_reducers = MultiValueField()
    software = MultiValueField()
    filters = MultiValueField()
    accessories = MultiValueField()

    rating = FloatField()
    integration = IntegerField()
    moon_phase = FloatField()
    first_acquisition_date = DateTimeField()
    last_acquisition_date = DateTimeField()
    views = IntegerField()

    solar_system_main_subject = IntegerField()

    is_deep_sky = BooleanField()
    is_clusters = BooleanField()
    is_nebulae = BooleanField()
    is_galaxies = BooleanField()

    is_solar_system = BooleanField()
    is_sun = BooleanField()
    is_moon = BooleanField()
    is_planets = BooleanField()
    is_comets = BooleanField()

    def index_queryset(self):
        return Image.objects.filter(Q(is_stored = True), Q(is_wip = False))

    def get_model(self):
        return Image

    def prepare_title(self, obj):
        value = obj.title

        match = re.match(r'.*\s+m\s*(?P<id>\d+).*', obj.title.lower())
        if match:
            value += ' Messier %s Messier%s' % (match.group('id'), match.group('id'))

        match = re.match(r'.*\s+messier\s*(?P<id>\d+).*', obj.title.lower())
        if match:
            value += ' M %s M%s' % (match.group('id'), match.group('id'))

        return value + ' ' + ''.join(value.split())

    def prepare_username(self, obj):
        return str(obj.user.username)

    def prepare_subjects(self, obj):
        # TODO: prepare also idlist
        subjects = []
        for s in obj.subjects.all():
            name = s.mainId
            mindreader = ""
            match = re.match(r'^m\s?(?P<id>\d+.*)', name.lower())
            if match:
                mindreader = 'Messier %s' % match.group('id')
            else:
                match = re.match(r'^messier\s?(?P<id>\d+.*)', name.lower())
                if match:
                    mindreader = 'M %s' % match.group('id')

            subjects.append(name)
            if mindreader != "":
                subjects.append(mindreader)

        return _join_stripped(subjects)

    def prepare_imaging_telescopes(self, obj):
        return _join_stripped([i.name for i in obj.imaging_telescopes.all()])

    def prepare_guiding_telescopes(self, obj):
        return _join_stripped([i.name for i in obj.guiding_telescopes.all()])

    def prepare_mounts(self, obj):
        return _join_stripped([i.name for i in obj.mounts.all()])

    def prepare_imaging_cameras(self, obj):
        return _join_stripped([i.name for i in obj.imaging_cameras.all()])

    def prepare_guiding_cameras(self, obj):
        return _join_stripped([i.name for i in obj.guiding_cameras.all()])

    def prepare_focal_reducers(self, obj):
        return _join_stripped([i.name for i in obj.focal_reducers.all()])

    def prepare_software(self, obj):
        return _join_stripped([i.name for i in obj.software.all()])

    def prepare_filters(self, obj):
        return _join_stripped([i.name for i in obj.filters.all()])

    def prepare_accessories(self, obj):
        return _join_stripped([i.name for i in obj.accessories.all()])

    def prepare_rating(self, obj):
        votes = obj.rating.votes
        score = obj.rating.score
        return float(score)/votes if votes > 0 else 0

    def prepare_integration(self, obj):
        return _get_integration(obj)

    def prepare_moon_phase(self, obj):
        from moon import MoonPhase

        deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=obj)
        moon_illuminated_list = []
        if deep_sky_acquisitions:
            for a in deep_sky_acquisitions:
                if a.date is not None:
                    m = MoonPhase(a.date)
                    moon_illuminated_list.append(m.illuminated * 100.0)

        if len(moon_illuminated_list) == 0:
            # We must make an assumption between 0 and 100, or this won't
            # show up in any searches.
            return 0

        return sum(moon_illuminated_list) / float(len(moon_illuminated_list))

    def prepare_first_acquisition_date(self, obj):
        deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=obj)
        solar_system_acquisition = None

        try:
            solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=obj)
        except:
            pass

        date = None
        if deep_sky_acquisitions:
            date = deep_sky_acquisitions[0].date
            for a in deep_sky_acquisitions:
                if a.date is not None and date is not None:
                    if a.date < date:
                        date = a.date
        elif solar_system_acquisition:
            date = solar_system_acquisition.date

        return date

    def prepare_last_acquisition_date(self, obj):
        deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=obj)
        solar_system_acquisition = None

        try:
            solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=obj)
        except:
            pass

        date = None
        if deep_sky_acquisitions:
            date = deep_sky_acquisitions[0].date
            for a in deep_sky_acquisitions:
                if a.date is not None and date is not None:
                    if a.date > date:
                        date = a.date
        elif solar_system_acquisition:
            date = solar_system_acquisition.date

        return date if date else datetime.datetime.min

    def prepare_views(self, obj):
        views = 0
        try:
            views = HitCount.objects.get(object_pk = obj.pk).hits
        except HitCount.DoesNotExist:
            pass

        return views
            
    def prepare_solar_system_main_subject(self, obj):
        return obj.solar_system_main_subject


    def prepare_is_deep_sky(self, obj):
        return DeepSky_Acquisition.objects.filter(image = obj).count() > 0

    def prepare_is_clusters(self, obj):
        for subject in obj.subjects.all():
            if subject.otype in ('GlC', 'GCl', 'OpC'):
                return True

        return False

    def prepare_is_nebulae(self, obj):
        for subject in obj.subjects.all():
            if subject.otype in ('Psr', 'HII', 'RNe', 'ISM', 'sh ', 'PN '):
                return True

        return False

    def prepare_is_galaxies(self, obj):
        for subject in obj.subjects.all():
            if subject.otype in ('LIN', 'IG', 'GiG', 'Sy2', 'G'):
                return True

        return False

    def prepare_is_solar_system(self, obj):
        if obj.solar_system_main_subject:
            return True

        if SolarSystem_Acquisition.objects.filter(image = obj):
            return True

        return False

    def prepare_is_sun(self, obj):
        return obj.solar_system_main_subject == 0

    def prepare_is_moon(self, obj):
        return obj.solar_system_main_subject == 1

    def prepare_is_planets(self, obj):
        return obj.solar_system_main_subject in range(2, 8)

    def prepare_is_comets(self, obj):
        return obj.solar_system_main_subject == 10


class SubjectIdentifierIndex(SearchIndex):
    text = NgramField(document=True, use_template=True)

    def index_queryset(self):
        return SubjectIdentifier.objects.all()

    def get_model(self):
        return SubjectIdentifier


class SubjectIndex(SearchIndex):
    text = NgramField(document=True, use_template=True)

    def index_queryset(self):
        return Subject.objects.all()

    def get_model(self):
        return Subject


site.register(Image, ImageIndex)
site.register(User, UserIndex)
site.register(SubjectIdentifier, SubjectIdentifierIndex)
site.register(Subject, SubjectIndex)
