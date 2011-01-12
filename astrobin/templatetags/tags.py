from django.template import Library
from django.conf import settings

register = Library() 

@register.simple_tag
def current(request, pattern):
    import re
    if re.search(pattern, request.path):
        return 'current'
    return ''


@register.inclusion_tag('image-list.html')
def image_list(objects_list):
    return {'image_list': [i.object for i in objects_list],
            'thumbnail_size':settings.THUMBNAIL_SIZE,
            's3_thumbnails_bucket':settings.S3_THUMBNAILS_BUCKET,
            's3_abpod_bucket':settings.S3_ABPOD_BUCKET,
            's3_url':settings.S3_URL,
           }

