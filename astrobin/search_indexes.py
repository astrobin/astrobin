from haystack.indexes import *
from haystack import site

from astrobin.models import Image
from astrobin.models import DeepSky_Acquisition
from astrobin.models import SolarSystem_Acquisition

class ImageIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    title = CharField(model_attr='title')
    user = CharField(model_attr='user')
    description = CharField(model_attr='description')
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

    rating = IntegerField()
    integration = IntegerField()
    uploaded = DateTimeField(model_attr='uploaded')

    def get_query(self):
        return Image.objects.all()

    def prepare_subjects(self, obj):
        return [subject.name for subject in obj.subjects.all()]

    def prepare_imaging_telescopes(self, obj):
        return [i.name for i in obj.imaging_telescopes.all()]

    def prepare_guiding_telescopes(self, obj):
        return [i.name for i in obj.guiding_telescopes.all()]

    def prepare_mounts(self, obj):
        return [i.name for i in obj.mounts.all()]

    def prepare_imaging_cameras(self, obj):
        return [i.name for i in obj.imaging_cameras.all()]

    def prepare_guiding_cameras(self, obj):
        return [i.name for i in obj.guiding_cameras.all()]

    def prepare_focal_reducers(self, obj):
        return [i.name for i in obj.focal_reducers.all()]

    def prepare_software(self, obj):
        return [i.name for i in obj.software.all()]

    def prepare_filters(self, obj):
        return [i.name for i in obj.filters.all()]

    def prepare_accessories(self, obj):
        return [i.name for i in obj.accessories.all()]

    def prepare_rating(self, obj):
        votes = obj.rating.votes
        score = obj.rating.score
        return float(score)/votes if votes > 0 else 0

    def prepare_integration(self, obj):
        deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=obj)
        solar_system_acquisition = None
        integration = 0

        try:
            solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=obj)
        except:
            pass

        if deep_sky_acquisitions:
            for a in deep_sky_acquisitions:
                if a.acquisition_type in ('l', 'r', 'g', 'b'):
                    integration += a.duration
        elif solar_system_acquisition:
            integration = solar_system_acquisition.frames

        return integration


site.register(Image, ImageIndex)

