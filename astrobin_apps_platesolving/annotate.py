import logging
import os
import six
if six.PY2:
    from StringIO import StringIO
else:
    from io import StringIO

import simplejson
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile

from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_platesolving.utils import get_from_storage, ThumbnailNotReadyException

log = logging.getLogger('apps')


class Annotator:
    def __init__(self, solution):
        self.solution = solution
        self.resampling_factor = 2.0
        self.line_thickness = 2 * int(round(self.resampling_factor))
        self.solver = Solver()

    def drawAnnotations(self, draw, annotations):
        def getAnnotationFont(annotation):
            font_path = os.path.join(os.getcwd(), 'astrobin/static/astrobin/fonts/arial.ttf')
            font_small = ImageFont.truetype(font_path, int(round(16 * self.resampling_factor)))
            font_medium = ImageFont.truetype(font_path, int(round(32 * self.resampling_factor)))
            font_large = ImageFont.truetype(font_path, int(round(48 * self.resampling_factor)))
            font_xlarge = ImageFont.truetype(font_path, int(round(64 * self.resampling_factor)))

            radius = annotation['radius']
            if radius < 10 * self.resampling_factor:
                font = font_small
            elif radius < 50 * self.resampling_factor:
                font = font_medium
            elif radius < 100 * self.resampling_factor:
                font = font_large
            else:
                font = font_xlarge

            return font

        def getAnnotationText(annotation):
            return ' / '.join(annotation['names'])

        def computeTextSize(annotation):
            font = getAnnotationFont(annotation)
            text = getAnnotationText(annotation)
            return font.getsize(text)

        def computeTextPadding(annotation):
            size = computeTextSize(annotation)
            return size[1] / 3

        def computeTextCoordinates(annotation):
            x, y = annotation['pixelx'], annotation['pixely']
            w, h = computeTextSize(annotation)

            coordinates = int(round(x - w / 2)), int(round(y - annotation['radius'] - h * 2))

            # If the object's radius extends beyond the image, the text would be outside of the image's bound.
            if coordinates[1] < 0:
                coordinates = int(round(x - w / 2)), int(round(y - h * 2))

            return coordinates

        def computeTextBoundingBox(annotation):
            x, y = computeTextCoordinates(annotation)
            w, h = computeTextSize(annotation)
            padding = computeTextPadding(annotation)
            box = {
                'x': x - padding,
                'y': y - padding,
                'w': w + padding * 2,
                'h': h + padding * 2
            }

            return box

        def computeColors(annotation, shape):
            semi_opaque_types = ['hd']

            white = (255, 255, 255)
            black = (0, 0, 0)
            semi_opaque_white = (255, 255, 255, 128)
            semi_opaque_black = (0, 0, 0, 128)

            if shape in ('circle', 'rectangle'):
                # Shape with a fill are half as opaque.
                white = (255, 255, 255, 128)
                black = (0, 0, 0, 128)
                semi_opaque_white = (255, 255, 255, 64)
                semi_opaque_black = (0, 0, 0, 64)

            if annotation['type'] in semi_opaque_types:
                return semi_opaque_white, semi_opaque_black
            return white, black

        # Unused for now
        def collisionDetected(annotation, others):
            box = computeTextBoundingBox(annotation)

            for o in others:
                other_box = computeTextBoundingBox(o)
                collision = (abs(box['x'] - other_box['x']) * 2 < (box['w'] + other_box['w'])) and \
                            (abs(box['y'] - other_box['y']) * 2 < (box['h'] + other_box['h']))
                if collision:
                    return True

            return False

        supported_types = ['m', 'ic', 'ngc', 'ugc', 'abel', 'bright', 'hd']
        annotations.sort(key=lambda x: x['radius'])
        for annotation in annotations:
            if annotation['type'] in supported_types:
                x = annotation['pixelx'] = annotation['pixelx'] * self.resampling_factor
                y = annotation['pixely'] = annotation['pixely'] * self.resampling_factor
                radius = annotation['radius'] = \
                    annotation['radius'] * self.resampling_factor + 10 * self.resampling_factor

                font = getAnnotationFont(annotation)
                text = getAnnotationText(annotation)
                text_x, text_y = computeTextCoordinates(annotation)
                box = computeTextBoundingBox(annotation)

                for i in range(0, self.line_thickness):
                    # Circle
                    draw.ellipse(
                        [x - radius + 1 + i, y - radius + 1 + i, x + radius - 1 - i, y + radius - 1 - i],
                        outline=computeColors(annotation, 'circle')[1])
                    draw.ellipse(
                        [x - radius - i, y - radius - i, x + radius + i, y + radius + i],
                        outline=computeColors(annotation, 'circle')[0])

                    # Line to text
                    if x > 0 and y - radius > 0 and box['y'] + box['h'] > 0:
                        draw.line(
                            [x + 1 + i, y - radius, x + 1 + i, box['y'] + box['h']],
                            computeColors(annotation, 'line')[1])
                        draw.line(
                            [x + i, y - radius, x + i, box['y'] + box['h']],
                            computeColors(annotation, 'line')[0])

                # Text box
                draw.rectangle(
                    [box['x'], box['y'], box['x'] + box['w'], box['y'] + box['h']],
                    outline=computeColors(annotation, 'rectangle')[0],
                    fill=computeColors(annotation, 'rectangle')[1])

                # Text
                draw.text((text_x + 1, text_y + 1), text, computeColors(annotation, 'text')[1], font)
                draw.text((text_x, text_y), text, computeColors(annotation, 'text')[0], font)

    def annotate(self):
        if self.solution.annotations is None:
            return None

        annotationsObj = None
        try:
            annotationsObj = simplejson.loads(self.solution.annotations)['annotations']
        except TypeError as e:
            log.warning("annotate.py: TypeError when trying to parse annotations: %s" % e.message)
            return None

        w, h = self.solution.content_object.w, self.solution.content_object.h
        if w:
            hd_w = settings.THUMBNAIL_ALIASES['']['hd']['size'][0]
            hd_h = int(round(h * hd_w / float(w)))
            if hd_w > w:
                hd_w = w
                hd_h = h

            try:
                base = Image.open(
                    get_from_storage(self.solution.content_object, 'hd')
                ).convert('RGBA')
            except ThumbnailNotReadyException as e:
                log.warning("annotate.py: ThumbnailNotReadyException when trying to open the image: %s" % e.message)
                return None
            except IOError as e:
                log.warning("annotate.py: IOError when trying to open the image: %s" % e.message)
                return None

            if self.resampling_factor != 1:
                base = base.resize(
                    (int(round(hd_w * self.resampling_factor)),
                     int(round(hd_h * self.resampling_factor))),
                    Image.ANTIALIAS)

            overlay = Image.new('RGBA', base.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            self.drawAnnotations(draw, annotationsObj)
            del draw

            image_io = StringIO()
            image = Image.alpha_composite(base, overlay)
            image = image.resize((hd_w, hd_h), Image.ANTIALIAS)
            image = image.convert('RGB')
            image.save(image_io, 'JPEG', quality=90, icc_profile=base.info.get('icc_profile'))

            return ContentFile(image_io.getvalue())

        return None
