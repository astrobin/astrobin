from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from astrobin.models import Image
from astrobin.image_utils import generate_histogram
from astrobin.storage import save_to_bucket

from PIL import Image as PILImage
import os
import urllib2
import tempfile
import StringIO

class Command(BaseCommand):
    help = "Regenerates all histograms."

    def handle(self, *args, **options):
        images = Image.objects.all()

        tempdir = tempfile.mkdtemp()
        for i in images:
            url = 'http://s3.amazonaws.com/astrobin_images/%s%s' % (i.filename, i.original_ext)
            path = os.path.join(tempdir, i.filename + i.original_ext)

            try:
                u = urllib2.urlopen(url)
            except:
                print i.filename + ": HTTP error."
                continue

            f = open(path, 'w')
            f.write(u.read())
            f.close()

            f = open(path, 'r')
            image = PILImage.open(f)
            try:
	        new_hist = generate_histogram(image)
            except:
                print i.filename + ": error generating histogram."
                f.close()
                os.remove(path)
                continue

            new_hist_f = StringIO.StringIO()
            new_hist.save(new_hist_f, 'PNG')
            save_to_bucket(i.filename + '_hist.png', new_hist_f.getvalue())
            
            f.close()
            os.remove(path)

            print i.filename + ": done."

        os.removedirs(tempdir)    

        print "All done."

