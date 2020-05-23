import logging
import os
from StringIO import StringIO

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
            return int(round(x - w / 2)), int(round(y - annotation['radius'] - h * 2))

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

        supported_types = ['m', 'ic', 'ngc', 'ugc', 'abel', 'bright']
        annotations.sort(key=lambda x: x['radius'])
        for annotation in annotations:
            if annotation['type'] in supported_types:
                x = annotation['pixelx'] = annotation['pixelx'] * self.resampling_factor
                y = annotation['pixely'] = annotation['pixely'] * self.resampling_factor
                radius = annotation['radius'] = \
                    annotation['radius'] * self.resampling_factor + 10 * self.resampling_factor
                white = (255, 255, 255)
                black = (0, 0, 0)

                font = getAnnotationFont(annotation)
                text = getAnnotationText(annotation)
                text_x, text_y = computeTextCoordinates(annotation)
                text_w, text_h = computeTextSize(annotation)
                box = computeTextBoundingBox(annotation)

                for i in range(0, self.line_thickness):
                    # Circle
                    draw.ellipse(
                        [x - radius + 1 + i, y - radius + 1 + i, x + radius - 1 - i, y + radius - 1 - i],
                        outline=black)
                    draw.ellipse(
                        [x - radius - i, y - radius - i, x + radius + i, y + radius + i],
                        outline=white)

                    # Line to text
                    draw.line(
                        [x + 1 + i, y - radius, x + 1 + i, box['y'] + box['h']],
                        black)
                    draw.line(
                        [x + i, y - radius, x + i, box['y'] + box['h']],
                        white)

                # Text box
                draw.rectangle(
                    [box['x'], box['y'], box['x'] + box['w'], box['y'] + box['h']],
                    outline=(255, 255, 255, 128),
                    fill=(0, 0, 0, 128))

                # Text
                draw.text((text_x + 1, text_y + 1), text, black, font)
                draw.text((text_x, text_y), text, white, font)

    def annotate(self):
        if self.solution.annotations is None:
            return None

        annotationsObj = None
        try:
            annotationsObj = simplejson.loads(self.solution.annotations)['annotations']
        except TypeError:
            return None

        w, h = self.solution.content_object.w, self.solution.content_object.h
        if w:
            hd_w = settings.THUMBNAIL_ALIASES['']['hd']['size'][0]
            hd_h = int(round(h * hd_w / float(w)))
            if hd_w > w:
                hd_w = w
                hd_h = h

            thumbnail_w = settings.THUMBNAIL_ALIASES['']['regular']['size'][0]
            thumbnail_h = int(round(h * thumbnail_w / float(w)))
            if thumbnail_w > w:
                thumbnail_w = w
                thumbnail_h = h

            try:
                base = Image \
                    .open(get_from_storage(
                    self.solution.content_object,
                    'hd',
                    '0' if not hasattr(self.solution.content_object, 'label')
                    else self.solution.content_object.label)) \
                    .convert('RGBA')
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
            image = image.resize((thumbnail_w, thumbnail_h), Image.ANTIALIAS)
            image = image.convert('RGB')
            image.save(image_io, 'JPEG', quality=90)

            return ContentFile(image_io.getvalue())

        return None
