import simplejson
from urllib import urlencode
from urllib2 import urlopen, Request, HTTPError

from django.conf import settings

from astrobin_apps_platesolving.backends.base import AbstractPlateSolvingBackend

from errors import MalformedResponse, RequestError
from utils import json2python, python2json


default_url = 'http://nova.astrometry.net/api/'


class Solver(AbstractPlateSolvingBackend):
    def __init__(self, apiurl = default_url):
        self.session = None
        self.apiurl = apiurl

    def get_url(self, service):
        return 'http://nova.astrometry.net/api/' + service

    def send_request(self, service, args={}, file_args=None):
        '''
        service: string
        args: dict
        '''
        if self.session is not None:
            args.update({ 'session' : self.session })
        print 'Python:', args
        json = python2json(args)
        print 'Sending json:', json
        url = self.get_url(service)
        print 'Sending to URL:', url

        # If we're sending a file, format a multipart/form-data
        if file_args is not None:
            m1 = MIMEBase('text', 'plain')
            m1.add_header('Content-disposition', 'form-data; name="request-json"')
            m1.set_payload(json)

            m2 = MIMEApplication(file_args[1],'octet-stream',encode_noop)
            m2.add_header('Content-disposition',
                          'form-data; name="file"; filename="%s"' % file_args[0])

            #msg.add_header('Content-Disposition', 'attachment',
            # filename='bud.gif')
            #msg.add_header('Content-Disposition', 'attachment',
            # filename=('iso-8859-1', '', 'FuSballer.ppt'))

            mp = MIMEMultipart('form-data', None, [m1, m2])

            # Makie a custom generator to format it the way we need.
            from cStringIO import StringIO
            from email.generator import Generator

            class MyGenerator(Generator):
                def __init__(self, fp, root=True):
                    Generator.__init__(self, fp, mangle_from_=False,
                                       maxheaderlen=0)
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
                        print >> self._fp, ('%s: %s\r\n' % (h,v)),
                    # A blank line always separates headers from body
                    print >> self._fp, '\r\n',

                # The _write_multipart method calls "clone" for the
                # subparts.  We hijack that, setting root=False
                def clone(self, fp):
                    return MyGenerator(fp, root=False)

            fp = StringIO()
            g = MyGenerator(fp)
            g.flatten(mp)
            data = fp.getvalue()
            headers = {'Content-type': mp.get('Content-type')}

            if False:
                print 'Sending headers:'
                print ' ', headers
                print 'Sending data:'
                print data[:1024].replace('\n', '\\n\n').replace('\r', '\\r')
                if len(data) > 1024:
                    print '...'
                    print data[-256:].replace('\n', '\\n\n').replace('\r', '\\r')
                    print

        else:
            # Else send x-www-form-encoded
            data = {'request-json': json}
            print 'Sending form data:', data
            data = urlencode(data)
            print 'Sending data:', data
            headers = {}

        request = Request(url=url, headers=headers, data=data)

        try:
            f = urlopen(request)
            txt = f.read()
            print 'Got json:', txt
            result = json2python(txt)
            print 'Got result:', result
            stat = result.get('status')
            print 'Got status:', stat
            if stat == 'error':
                errstr = result.get('errormessage', '(none)')
                raise RequestError('server error message: ' + errstr)
            return result
        except HTTPError, e:
            print 'HTTPError', e
            txt = e.read()
            open('err.html', 'wb').wzypr***REMOVED***rite(txt)
            print 'Wrote error text to err.html'


    def login(self, apikey):
        args = {'apikey': apikey}

        result = self.send_request('login', args)
        session = result.get('session')
        print 'Got session:', session

        if not session:
            raise RequestError('no session in result')
        self.session = session


    def start(self, image):
        apikey = settings.ASTROMETRY_NET_API_KEY
        self.login(apikey)

