import logging
from email.encoders import encode_noop
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from urllib import urlencode
from urllib2 import urlopen, Request

import requests
from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from astrobin_apps_platesolving.backends.base import AbstractPlateSolvingBackend
from errors import RequestError
from utils import json2python, python2json

default_url = 'http://nova.astrometry.net/api/'

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
            m1 = MIMEBase('text', 'plain')
            m1.add_header('Content-disposition', 'form-data; name="request-json"')
            m1.set_payload(json)

            m2 = MIMEApplication(file_args[1], 'octet-stream', encode_noop)
            m2.add_header(
                'Content-disposition',
                'form-data; name="file"; filename="%s"' % file_args[0])

            mp = MIMEMultipart('form-data', None, [m1, m2])

            # Make a custom generator to format it the way we need.
            from cStringIO import StringIO
            from email.generator import Generator

            class MyGenerator(Generator):
                def __init__(self, fp, root=True):
                    Generator.__init__(self, fp, mangle_from_=False, maxheaderlen=0)
                    self.root = root

                def _write_headers(self, msg):
                    # We don't want to write the top-level headers;
                    # they go into Request(headers) instead.
                    if self.root:
                        return

                    # We need to use \r\n line-terminator, but Generator
                    # doesn't provide the flexibility to override, so we
                    # have to copy-n-paste-n-modify.
                    for h, v in msg.items():
                        print >> self._fp, ('%s: %s\r\n' % (h, v)),

                    # A blank line always separates headers from body
                    print >> self._fp, '\r\n',

                # The _write_multipart method calls "clone" for the
                # sub-parts.  We hijack that, setting root=False.
                def clone(self, fp):
                    return MyGenerator(fp, root=False)

            fp = StringIO()
            g = MyGenerator(fp)
            g.flatten(mp)
            data = fp.getvalue()
            headers = {'Content-type': mp.get('Content-type')}
        else:
            # Else send x-www-form-encoded
            data = {'request-json': json}
            data = urlencode(data)
            headers = {}

        log.debug("Astrometry.net: sending request to %s" % url)
        request = Request(url=url, headers=headers, data=data)

        response = urlopen(request)
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
            return 'http://nova.astrometry.net/annotated_full/%d' % job_id

        return ''

    def sky_plot_zoom1_image_url(self, submission_id):
        job_calibration_id = self.get_job_calibration_from_submission(submission_id)

        if job_calibration_id:
            return 'http://nova.astrometry.net/sky_plot/zoom1/%d' % job_calibration_id

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
