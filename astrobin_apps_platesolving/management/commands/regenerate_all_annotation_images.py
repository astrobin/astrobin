# coding=utf-8
import requests
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from astrobin.models import Image, ImageRevision


class Command(BaseCommand):
    help = "Find images with missing annotation file and regenerate it."

    def handle(self, *args, **options):
        count_images = 0
        count_revisions = 0
        for user in User.objects.all():
            print "%s:" % user.username
            images = Image.objects_including_wip.filter(user=user).exclude(corrupted=True)
            for image in images:
                print "  - %d " % image.pk,
                if image.solution and image.solution.annotations:
                    try:
                        r = requests.get(image.solution.image_file.url, verify=False)
                        if r.status_code != 200:
                            print "X ",
                            requests.post("https://www.astrobin.com/platesolving/finalize/%d/" % image.solution.pk)
                            count_images += 1
                            print "✓"
                        else:
                            print "✓"
                    except:
                        print "/"
                else:
                    print "/"

                revisions = ImageRevision.objects.filter(image=image).exclude(corrupted=True)
                for revision in revisions:
                    print "    - %s " % revision.label,
                    if revision.solution and revision.solution.annotations:
                        try:
                            r = requests.get(revision.solution.revision_file.url, verify=False)
                            if r.status_code != 200:
                                print "X ",
                                requests.post("https://www.astrobin.com/platesolving/finalize/%d/" % revision.solution.pk)
                                count_revisions =+ 1
                                print "✓"
                            else:
                                print "✓"
                        except:
                            print "/"
                    else:
                        print "/"

        print "Fixed %d images and %d revisions" % (count_images, count_revisions)
