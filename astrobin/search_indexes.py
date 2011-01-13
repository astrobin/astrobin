from haystack.indexes import *
from haystack import site
from astrobin.models import Image

class ImageIndex(SearchIndex):
    text = CharField(document=True, use_template=True)
    title = CharField(model_attr='title')
    user = CharField(model_attr='user')
    description = CharField(model_attr='description')
    subjects = MultiValueField()
    gear = MultiValueField()

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


site.register(Image, ImageIndex)

