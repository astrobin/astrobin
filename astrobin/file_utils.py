from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings

import mimetypes
from uuid import uuid4
from PIL import Image as PILImage
from PIL import ImageOps
from PIL import ImageDraw
import StringIO

from models import Image


# RGB Hitogram
# This script will create a histogram image based on the RGB content of
# an image. It uses PIL to do most of the donkey work but then we just
# draw a pretty graph out of it.
#
# May 2009,  Scott McDonough, www.scottmcdonough.co.uk
#
def generate_histogram(img):
    histHeight = 120            # Height of the histogram
    histWidth = 256             # Width of the histogram
    multiplerValue = 1.5        # The multiplier value basically increases
                                # the histogram height so that love values
                                # are easier to see, this in effect chops off
                                # the top of the histogram.
    showFstopLines = True       # True/False to hide outline
    fStopLines = 5

    # Colours to be used
    backgroundColor = (84,59,43)    # Background color
    lineColor = (102,102,102)       # Line color of fStop Markers 
    red = (255,60,60)               # Color for the red lines
    green = (51,204,51)             # Color for the green lines
    blue = (0,102,255)              # Color for the blue lines
    ##################################################################################
    hist = img.histogram()
    histMax = max(hist)                                     # comon color
    xScale = float(histWidth)/len(hist)                     # xScaling
    yScale = float((histHeight)*multiplerValue)/histMax     # yScaling 

    im = PILImage.new("RGBA", (histWidth, histHeight), backgroundColor)   
    draw = ImageDraw.Draw(im)

    # Draw Outline is required
    if showFstopLines:    
        xmarker = histWidth/fStopLines
        x =0
        for i in range(1,fStopLines+1):
            draw.line((x, 0, x, histHeight), fill=lineColor)
            x+=xmarker
        draw.line((histWidth-1, 0, histWidth-1, 200), fill=lineColor)
        draw.line((0, 0, 0, histHeight), fill=lineColor)

    # Draw the RGB histogram lines
    x=0; c=0;
    for i in hist:
        if int(i)==0: pass
        else:
            color = red
            if c>255: color = green
            if c>511: color = blue
            draw.line((x, histHeight, x, histHeight-(i*yScale)), fill=color)        
        if x>255: x=0
        else: x+=1
        c+=1

    return im


def store_image_in_s3(file, uid, mimetype=''):
    def scale_dimensions(w, h, longest_side):
        if w > longest_side:
            ratio = longest_side*1./w
        elif h > longest_side:
            ratio = longest_side*1./h
        else:
            ratio = 1

        return (int(w*ratio), int(h*ratio))

    def scale_dimensions_for_cropping(w, h, shortest_side):
        if w < shortest_side and h < shortest_side:
            return (w, h)
        if w > h:
            ratio = shortest_side*1./h
        else:
            ratio = shortest_side*1./w

        return (int(w*ratio), int(h*ratio))

    def crop_box(w, h):
        if w > h:
            return ((w-h)/2, 0, (w+h)/2, h)
        elif h > w:
            return (0, (h-w)/2, w, (h+w)/2)
        return (0, 0, w, h)

    def save_to_bucket(data, content_type, bucket, uid):
        b = conn.create_bucket(bucket)
        k = Key(b)
        k.key = uid
        k.set_metadata("Content-Type", content_type)
        k.set_contents_from_string(data)
        k.set_acl("public-read");

    conn = S3Connection(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)
    content_type = mimetype if mimetype else mimetypes.guess_type(file.name)[0]
    data = StringIO.StringIO(file.read())

    # First store the original image
    save_to_bucket(data.getvalue(), content_type, settings.S3_IMAGES_BUCKET, uid)

    image = PILImage.open(data)
    # create histogram and store it
    histogram = generate_histogram(image)
    histogramFile = StringIO.StringIO()
    histogram.save(histogramFile, 'JPEG')
    save_to_bucket(histogramFile.getvalue(), 'image/jpeg', settings.S3_HISTOGRAMS_BUCKET, uid)

    # Then resize to the display image
    (w, h) = image.size
    (w, h) = scale_dimensions(w, h, settings.RESIZED_IMAGE_SIZE)
    resizedImage = image.resize((w, h), PILImage.ANTIALIAS)

    # Then save to bucket
    resizedFile = StringIO.StringIO()
    resizedImage.save(resizedFile, 'JPEG')
    save_to_bucket(resizedFile.getvalue(), 'image/jpeg', settings.S3_RESIZED_IMAGES_BUCKET, uid)

    # Then resize to the thumbnail
    (w, h) = image.size
    (w, h) = scale_dimensions_for_cropping(w, h, settings.THUMBNAIL_SIZE)
    thumbnailImage = image.resize((w, h), PILImage.ANTIALIAS)
    croppedImage = thumbnailImage.crop(crop_box(w, h))

    # Then save to bucket
    thumbnailFile = StringIO.StringIO()
    croppedImage.save(thumbnailFile, 'JPEG')
    save_to_bucket(thumbnailFile.getvalue(), 'image/jpeg', settings.S3_THUMBNAILS_BUCKET, uid)

    # Shrink more!
    (w, h) = image.size
    (w, h) = scale_dimensions_for_cropping(w, h, settings.SMALL_THUMBNAIL_SIZE)
    thumbnailImage = image.resize((w, h), PILImage.ANTIALIAS)
    croppedImage = thumbnailImage.crop(crop_box(w, h))

    # To the final bucket
    thumbnailFile = StringIO.StringIO()
    croppedImage.save(thumbnailFile, 'JPEG')
    save_to_bucket(thumbnailFile.getvalue(), 'image/jpeg', settings.S3_SMALL_THUMBNAILS_BUCKET, uid)

    # Let's also created a grayscale inverted image
    grayscale = ImageOps.grayscale(image)
    inverted = ImageOps.invert(grayscale)
    invertedFile = StringIO.StringIO()
    inverted.save(invertedFile, 'JPEG')
    save_to_bucket(invertedFile.getvalue(), 'image/jpeg', settings.S3_INVERTED_BUCKET, uid)

    # Then we invert the resized image too
    grayscale = ImageOps.grayscale(resizedImage)
    inverted = ImageOps.invert(grayscale)
    invertedFile = StringIO.StringIO()
    inverted.save(invertedFile, 'JPEG')
    save_to_bucket(invertedFile.getvalue(), 'image/jpeg', settings.S3_RESIZED_INVERTED_BUCKET, uid)

