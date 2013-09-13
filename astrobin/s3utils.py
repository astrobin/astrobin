from storages.backends.s3boto import S3BotoStorage

StaticRootS3BotoStorage = lambda: S3BotoStorage(location='static')
ImageRootS3BotoStorage  = lambda: S3BotoStorage(location='images')
