import logging
from email.encoders import encode_noop
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import requests
from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from astrobin_apps_platesolving.backends.base import AbstractPlateSolvingBackend
from .errors import RequestError
from .utils import json2python, python2json

base_url = 'http://nova.astrometry.net'
default_url = base_url + '/api/'

log = logging.getLogger('apps')


class Solver(AbstractPlateSolvingBackend):
    def __init__(self, api_url=default_url):
        self.session = None
        self.api_url = api_url

    def get_url(self, service):
        return 'http://nova.astrometry.net/api/' + service

    def send_request(self, service, args={}, file_args=None):
        if self.session is not None:
            args.update({'session': self.session})

        json = python2json(args)
        url = self.get_url(service)

        # If we're sending a file, format a multipart/form-data
        if file_args is not None:
            import random
            boundary_key = ''.join([random.choice('0123456789') for i in range(19)])
            boundary = '===============%s==' % boundary_key
            headers = {'Content-Type':
                           'multipart/form-data; boundary="%s"' % boundary}
            data_pre = (
                    '--' + boundary + '\n' +
                    'Content-Type: text/plain\r\n' +
                    'MIME-Version: 1.0\r\n' +
                    'Content-disposition: form-data; name="request-json"\r\n' +
                    '\r\n' +
                    json + '\n' +
                    '--' + boundary + '\n' +
                    'Content-Type: application/octet-stream\r\n' +
                    'MIME-Version: 1.0\r\n' +
                    'Content-disposition: form-data; name="file"; filename="%s"' % file_args[0] +
                    '\r\n' + '\r\n')
            data_post = (
                    '\n' + '--' + boundary + '--\n')
            data = data_pre.encode() + file_args[1] + data_post.encode()
        else:
            # Else send x-www-form-encoded
            data = {'request-json': json}
            data = urlencode(data)
            data = data.encode('utf-8')
            headers = {}

        request = Request(url=url, headers=headers, data=data)

        try:
            response = urlopen(request, timeout=30)
        except HTTPError as e:
            error_message = str(e)
            log.error("Astrometry.net request error: %s" % error_message)
            raise RequestError('Server error message: ' + error_message)

        text = response.read()
        result = json2python(text)
        status = result.get('status')

        if status == 'error':
            error_message = result.get('errormessage', '(none)')
            log.error("Astrometry.net request error: %s" % error_message)
            raise RequestError('Server error message: ' + error_message)

        return result

    def upload(self, f, **kwargs):
        args = self._get_upload_args(**kwargs)
        try:
            result = self.send_request('upload', args, (f.name, f.read()))
            return result
        except IOError:
            log.debug("File %s does not exist" % f.name)
            raise

    def url_upload(self, url, **kwargs):
        args = dict(url=url)
        args.update(self._get_upload_args(**kwargs))
        result = self.send_request('url_upload', args)
        return result

    def login(self, apikey):
        result = self.send_request('login', {'apikey': apikey})
        if result is None:
            raise RequestError('No result after login')

        session = result.get('session')
        if not session:
            raise RequestError('No session in result')

        self.session = session

    def start(self, image_url, **kwargs):
        self.login(settings.ASTROMETRY_NET_API_KEY)

        headers = {'User-Agent': 'Mozilla/5.0'}

        if 'https://' in image_url:
            r = requests.get(image_url, verify=False, allow_redirects=True, headers=headers)
        else:
            r = requests.get(image_url, allow_redirects=True, headers=headers)

        f = NamedTemporaryFile(delete=True)
        f.write(r.content)
        f.flush()
        f.seek(0)

        upload = self.upload(File(f), **kwargs)

        if upload['status'] == 'success':
            return upload['subid']

        return 0

    def job_status(self, job_id):
        result = self.send_request('jobs/%s' % job_id)
        return result

    def submission_status(self, submission_id):
        return self.send_request('submissions/%s' % submission_id)

    def get_job_from_submission(self, submission_id):
        s = self.submission_status(submission_id)
        jobs = s.get('jobs', [])

        if not jobs or jobs[0] == None:
            return None

        return jobs[0]

    def get_job_calibration_from_submission(self, submission_id):
        status = self.submission_status(submission_id)
        calibration = status.get('job_calibrations', [[]])

        if not calibration or calibration[0] == []:
            return None

        return calibration[0][1]

    def info(self, submission_id):
        job_id = self.get_job_from_submission(submission_id)

        if job_id:
            return self.send_request('jobs/%d/info' % job_id)

        return {}

    def annotations(self, submission_id):
        job_id = self.get_job_from_submission(submission_id)
        result = None

        if job_id:
            result = self.send_request('jobs/%s/annotations/' % job_id)

        return result

    def annotated_image_url(self, submission_id):
        job_id = self.get_job_from_submission(submission_id)

        if job_id:
            return '%s/annotated_full/%d' % (base_url, job_id)

        return ''

    def sky_plot_zoom1_image_url(self, submission_id):
        job_calibration_id = self.get_job_calibration_from_submission(submission_id)

        if job_calibration_id:
            return '%s/sky_plot/zoom1/%d' % (base_url, job_calibration_id)

        return ''

    def _get_upload_args(self, **kwargs):
        args = {}

        for key, default, typ in [
            ('allow_commercial_use', 'n', str),
            ('allow_modifications', 'n', str),
            ('publicly_visible', 'n', str),
            ('scale_units', None, str),
            ('scale_type', None, str),
            ('scale_lower', None, float),
            ('scale_upper', None, float),
            ('scale_est', None, float),
            ('scale_err', None, float),
            ('center_ra', None, float),
            ('center_dec', None, float),
            ('radius', None, float),
            ('downsample_factor', None, int),
            ('tweak_order', None, int),
            ('crpix_center', None, bool),
        ]:
            if key in kwargs:
                val = kwargs.pop(key)
                if val is not None:
                    val = typ(val)
                    args.update({key: val})
            elif default is not None:
                args.update({key: default})

        return args
