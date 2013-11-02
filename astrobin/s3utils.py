from storages.backends.s3boto import S3BotoStorage
from pipeline.storage import PipelineMixin

ImageRootS3BotoStorage = lambda: S3BotoStorage(location='images')

class S3PipelineStorage(PipelineMixin, S3BotoStorage):
    pass
StaticRootS3BotoStorage = lambda: S3PipelineStorage(location='www/static')
