from tastypie.resources import ModelResource, ALL
from tastypie import fields

from astrobin.models import Image, ImageRevision, Subject, SubjectIdentifier, \
                            Comment

class SubjectResource(ModelResource):
    identifiers = fields.ToManyField('astrobin.api.SubjectIdentifierResource', 'idlist')

    class Meta:
        queryset = Subject.objects.all()
        allowed_methods = ['get']


class SubjectIdentifierResource(ModelResource):
    subject = fields.ForeignKey(SubjectResource, 'subject')

    class Meta:
        queryset = SubjectIdentifier.objects.all()
        allowed_methods = ['get']


class CommentResource(ModelResource):
    image = fields.ForeignKey('astrobin.api.ImageResource', 'image')
    author = fields.CharField()
    replies = fields.ToManyField('self', 'children')

    class Meta:
        queryset = Comment.objects.all()
        fields = ['comment', 'added']

    def dehydrate_comment(self, bundle):
        if bundle.obj.is_deleted:
            return '(comment deleted)'
        return bundle.data['comment']

    def dehydrate_author(self, bundle):
        return bundle.obj.author.username


class ImageRevisionResource(ModelResource):
    image = fields.ForeignKey('astrobin.api.ImageResource', 'image')

    class Meta:
        queryset = ImageRevision.objects.all()
        fields = [
            'uploaded',
            'w',
            'h',
            'is_solved',
            'is_final',
        ]
        allowed_methods = ['get']
    

class ImageResource(ModelResource):
    author = fields.CharField()
    revisions = fields.ToManyField(ImageRevisionResource, 'imagerevision_set')

    subjects = fields.ToManyField(SubjectResource, 'subjects')

    imaging_telescopes = fields.ListField()
    imaging_cameras = fields.ListField()

    comments = fields.ToManyField(CommentResource, 'comment_set')

    class Meta:
        queryset = Image.objects.filter(is_stored = True, is_wip = False)
        fields = [
            'id',
            'author',
            'title',
            'uploaded',
            'updated',
            'description',
            'h',
            'w',
            'animated',
            'link',
            'link_to_fits',
            'rating_score',
            'rating_votes',
            'is_solved',
            'license',

            'is_final',

            'ra_center_hms',
            'dec_center_dms',
            'orientation',
            'pixel_scale',
            'fieldw',
            'fieldh',
            'fieldunits',
        ]
        allowed_methods = ['get']
        filtering = {
            'title': ALL,
            'is_solved': ('exact',),
            'author': ALL,
            'uploaded': ALL,
            'fieldw': ALL,
            'fieldh': ALL,
            'fieldunits': ALL,
        }

    def dehydrate_imaging_telescopes(self, bundle):
        telescopes = bundle.obj.imaging_telescopes.all()
        return [x.name for x in telescopes]

    def dehydrate_imaging_cameras(self, bundle):
        cameras = bundle.obj.imaging_cameras.all()
        return [x.name for x in cameras]

    def dehydrate_author(self, bundle):
        return bundle.obj.user.username

    def build_filters(self, filters = None):
        if filters is None:
            filters = {}

        orm_filters = super(ImageResource, self).build_filters(filters)

        #if 'author' in filters:
        #   qs = Image.objects.filter(user__username = filters['author'])
        #   orm_filters['pk__in'] = [i.pk for i in qs]

        return orm_filters
