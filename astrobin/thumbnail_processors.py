import os

from django.conf import settings

from PIL import Image, ImageOps, ImageDraw, ImageEnhance, ImageFont


def rounded_corners(image, rounded = False, **kwargs):
    if rounded:
        mask = Image.open('astrobin/thumbnail-mask.png').convert('L')
        mask = mask.resize(image.size, Image.ANTIALIAS)
        image = ImageOps.fit(image, mask.size, centering = (0.5, 0.5))
        image.putalpha(mask)

    return image


def invert(image, invert = False, **kwargs):
    if invert:
        image = ImageOps.grayscale(image)
        image = ImageOps.invert(image)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)

    return image


def annotate(image, annotate = False, **kwargs):
    if annotate:
        solution = kwargs.pop('solution')
        if solution:
            annotation = Image.open(solution.image_file.file)
            annotation = annotation.resize(image.size, Image.ANTIALIAS)
            image.paste(annotation, None, annotation)

    return image


def annotate_overlay(image, annotate_overlay = False, **kwargs):
    if annotate_overlay:
        solution = kwargs.pop('solution')
        if solution:
            annotation = Image.open(solution.image_file.file)
            annotation = annotation.resize(image.size, Image.ANTIALIAS)
            return annotation

    return image


def watermark(image, watermark = False, **kwargs):
    if watermark:
        try:
            text = kwargs['watermark_text']
            position = kwargs['watermark_position']
            opacity = kwargs['watermark_opacity']
        except KeyError:
            return image

        if text:
            watermark_image = Image.new('RGBA', image.size)
            draw = ImageDraw.Draw(watermark_image, 'RGBA')
            fontsize = 1
            ttf = os.path.join(settings.STATIC_ROOT, 'fonts/arial.ttf')

            img_fraction = 0.33

            font = ImageFont.truetype(ttf, fontsize)
            while font.getsize(text)[0] < img_fraction*image.size[0]:
                # iterate until the text size is just larger than the criteria
                fontsize += 1
                font = ImageFont.truetype(ttf, fontsize)

            # de-increment to be sure it is less than criteria
            fontsize -= 1
            font = ImageFont.truetype(ttf, fontsize)

            if position == 0:
                pos = (image.size[0] * .5 - font.getsize(text)[0] * .5,
                       image.size[1] * .5 - font.getsize(text)[1] * .5)
            elif position == 1:
                pos = (image.size[0] * .02,
                       image.size[1] * .02)
            elif position == 2:
                pos = (image.size[0] * .5 - font.getsize(text)[0] * .5,
                       image.size[1] * .02)
            elif position == 3:
                pos = (image.size[0] * .98 - font.getsize(text)[0],
                       image.size[1] * .02)
            elif position == 4:
                pos = (image.size[0] * .02,
                       image.size[1] * .98 - font.getsize(text)[1])
            elif position == 5:
                pos = (image.size[0] * .5 - font.getsize(text)[0] * .5,
                       image.size[1] * .98 - font.getsize(text)[1])
            elif position == 6:
                pos = (image.size[0] * .98 - font.getsize(text)[0],
                       image.size[1] * .98 - font.getsize(text)[1])

            draw.text(pos, text, font=font)
            mask = watermark_image.convert('L').point(lambda x: min(x, opacity))
            watermark_image.putalpha(mask)
            image.paste(watermark_image, None, watermark_image)

    return image


# RGB Hitogram
# This script will create a histogram image based on the RGB content of
# an image. It uses PIL to do most of the donkey work but then we just
# draw a pretty graph out of it.
#
# May 2009,  Scott McDonough, www.scottmcdonough.co.uk
#
def histogram(image, histogram = False, **kwargs):
    if not histogram:
        return image

    histWidth = kwargs['size'][0]  # Width of the histogram
    histHeight = kwargs['size'][1] # Height of the histogram
    multiplerValue = 1.0           # The multiplier value basically increases
                                   # the histogram height so that love values
                                   # are easier to see, this in effect chops off
                                   # the top of the histogram.
    showFstopLines = True          # True/False to hide outline
    fStopLines = 5

    # Colours to be used
    backgroundColor = (0,0,0,0)     # Background color
    lineColor = (102,102,102)       # Line color of fStop Markers
    red = (255,60,60)               # Color for the red lines
    green = (51,204,51)             # Color for the green lines
    blue = (0,102,255)              # Color for the blue lines
    ##################################################################################
    hist = image.histogram()
    histMax = max(hist)                                     # comon color
    xScale = float(histWidth)/len(hist)                     # xScaling
    yScale = float((histHeight)*multiplerValue)/histMax     # yScaling

    im = Image.new("RGBA", (histWidth, histHeight), backgroundColor)
    red_layer = Image.new("RGBA", (histWidth, histHeight), red)
    green_layer = Image.new("RGBA", (histWidth, histHeight), green)
    blue_layer = Image.new("RGBA", (histWidth, histHeight), blue)
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
            alpha_mask = Image.new("L", (histWidth, histHeight), 0)
            alpha_mask_draw = ImageDraw.Draw(alpha_mask)
            alpha_mask_draw.line((x, histHeight, x, histHeight - (i * yScale)), fill = 128)
            if color == red:
                im = Image.composite(red_layer, im, alpha_mask)
            elif color == green:
                im = Image.composite(green_layer, im, alpha_mask)
            elif color == blue:
                im = Image.composite(blue_layer, im, alpha_mask)
        if x > 255:
            x=0
        else:
            x += 1
        c += 1

    return im

