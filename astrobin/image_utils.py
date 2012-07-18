from django.conf import settings

from astrobin.storage import save_to_bucket

from PIL import Image as PILImage
from PIL import ImageOps
from PIL import ImageDraw

import os
import urllib2
import tempfile
import StringIO
from datetime import datetime


def scale_dimensions_for_cropping(w, h, shortest_side):
    if w < shortest_side and h < shortest_side:
        return (w, h)
    if w > h:
        ratio = shortest_side*1./h
    else:
        ratio = shortest_side*1./w

    return (int(w*ratio), int(h*ratio))


def scale_dimensions(w, h, longest_side):
    if w > longest_side:
        ratio = longest_side*1./w
    else:
        ratio = 1

    return (int(w*ratio), int(h*ratio))


def crop_box(w, h):
    if w > h:
        return ((w-h)/2, 0, (w+h)/2, h)
    elif h > w:
        return (0, (h-w)/2, w, (h+w)/2)
    return (0, 0, w, h)

def crop_box_max(w, h, max_w, max_h):
    if max_w > w and max_h > h:
        return (0, 0, w, h)

    mid_w = w * .5
    mid_h = h * .5

    return (int(mid_w - max_w * .5), int(mid_h - max_h * .5),
            int(mid_w + max_w * .5), int(mid_h + max_h * .5))


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
    multiplerValue = 1.0        # The multiplier value basically increases
                                # the histogram height so that love values
                                # are easier to see, this in effect chops off
                                # the top of the histogram.
    showFstopLines = True       # True/False to hide outline
    fStopLines = 5

    # Colours to be used
    backgroundColor = (0,0,0,0)     # Background color
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
    red_layer = PILImage.new("RGBA", (histWidth, histHeight), red)
    green_layer = PILImage.new("RGBA", (histWidth, histHeight), green)
    blue_layer = PILImage.new("RGBA", (histWidth, histHeight), blue)
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
    x = 0;
    c = 0;
    for i in hist:
        if int(i) == 0:
            pass
        else:
            color = red
            if c > 255:
                color = green
            if c > 511:
                color = blue
            # Wow, we could _not_ be any slower here. :-/
            alpha_mask = PILImage.new("L", (histWidth, histHeight), 0)
            alpha_mask_draw = ImageDraw.Draw(alpha_mask)
            alpha_mask_draw.line((x, histHeight, x, histHeight - (i * yScale)), fill = 128)        
            if color == red:
                im = PILImage.composite(red_layer, im, alpha_mask)
            elif color == green:
                im = PILImage.composite(green_layer, im, alpha_mask)
            elif color == blue:
                im = PILImage.composite(blue_layer, im, alpha_mask)
        if x > 255:
            x=0
        else:
            x += 1
        c += 1

    return im


def make_image_of_the_day(image):
    from astrobin.models import Image, ImageRevision, ImageOfTheDay

    filename = image.filename
    extension = image.original_ext

    if not image.is_final:
        print "Finding final revision..."
        revisions = ImageRevision.objects.filter(image = image)
        for revision in revisions:
            if revision.is_final:
                print "Found it."
                filename = revision.filename
                extension = revision.original_ext

    tempdir = tempfile.mkdtemp()
    url = 'http://s3.amazonaws.com/%s/%s%s' \
          % (settings.AWS_STORAGE_BUCKET_NAME, filename, extension)
    path = os.path.join(filename + extension)

    try:
        print "Getting file from S3..."
        u = urllib2.urlopen(url)
    except:
        print filename + ": HTTP error."
        return

    print "Saving file..."
    f = open(path, 'w')
    f.write(u.read())
    f.close()

    print "Reading file..."
    f = open(path, 'r')
    pil_image = PILImage.open(f)

    print "Resizing..."
    (w, h) = pil_image.size
    (w, h) = scale_dimensions(w, h, settings.IMAGE_OF_THE_DAY_WIDTH)
    pil_image = pil_image.resize((w, h), PILImage.ANTIALIAS)
    (w, h) = pil_image.size
    print "New size = (%d, %d)." % (w, h)

    print "Cropping..."
    (x1, y1, x2, y2) = crop_box_max(w, h,
                          settings.IMAGE_OF_THE_DAY_WIDTH,
                          settings.IMAGE_OF_THE_DAY_HEIGHT)

    print "Cropping to (%d, %d, %d, %d)..." % (x1, y1, x2, y2)
    pil_image = pil_image.crop((x1, y1, x2, y2))

    print "Dumping content..."
    f2 = StringIO.StringIO()
    if pil_image.mode != 'RGB' and pil_image.mode != 'I':
        pil_image = pil_image.convert('RGB')
    pil_image.save(f2, 'JPEG', quality=100)

    print "Saving to S3..."
    save_to_bucket(filename + '_iotd.jpg', f2.getvalue())
    
    print "See if there's an existing image for today..."
    today = datetime.now().date()
    try:
        iotd = ImageOfTheDay.objects.get(date = today)
        iotd.image = image
        print "Overwritten old entry."
    except ImageOfTheDay.DoesNotExist:
        iotd = ImageOfTheDay(image = image)
        print "Created new entry."

    iotd.filename = filename + '_iotd'
    iotd.save()

    print "Cleaning up..."
    f.close()
    f2.close()
    os.remove(path)
    os.removedirs(tempdir)    

    print "Done."

