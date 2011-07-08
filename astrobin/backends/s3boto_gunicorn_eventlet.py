"""
File backends with small tweaks to work with gunicorn + eventlet async
workers. These should eventually becom unecessary as the supporting libraries
continue to improve.
"""
import eventlet
from athumb.backends.s3boto import S3BotoStorage, S3BotoStorage_AllPublic

def eventlet_workaround(bytes_transmitted, bytes_remaining):
    """
    Stinks we have to do this, but calling this at intervals keeps gunicorn
    eventlet async workers from hanging and expiring.
    """
    eventlet.sleep(0)

class EventletS3BotoStorage(S3BotoStorage):
    """
    Modified standard S3BotoStorage class to play nicely with large file
    uploads and eventlet gunicorn workers.
    """
    def __init__(self, *args, **kwargs):
        super(EventletS3BotoStorage, self).__init__(*args, **kwargs)
        # Use the workaround as Boto's set_contents_from_file() callback.
        self.s3_callback_during_upload = eventlet_workaround
        
class EventletS3BotoStorage_AllPublic(S3BotoStorage_AllPublic):
    """
    Modified standard S3BotoStorage_AllPublic class to play nicely with large 
    file uploads and eventlet gunicorn workers.
    """
    def __init__(self, *args, **kwargs):
        super(EventletS3BotoStorage_AllPublic, self).__init__(*args, **kwargs)
        # Use the workaround as Boto's set_contents_from_file() callback.
        self.s3_callback_during_upload = eventlet_workaround