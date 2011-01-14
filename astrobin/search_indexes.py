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
    gear = MultiValueField()

    rating = IntegerField()
    integration = IntegerField()
    uploaded = DateTimeField(model_attr='uploaded')

    def get_query(self):
        return Image.objects.all()

    def prepare_subjects(self, obj):
        return [subject.name for subject in obj.subjects.all()]

    def prepare_gear(self, obj):
        list = []
        for g in (obj.imaging_telescopes, obj.guiding_telescopes, obj.mounts,
                  obj.imaging_cameras, obj.guiding_cameras,
                  obj.focal_reducers, obj.software, obj.filters,
                  obj.accessories):
            list.extend([i.name for i in g.all()])

        return list

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

