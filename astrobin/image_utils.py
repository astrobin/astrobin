from PIL import Image as PILImage
from PIL import ImageOps
from PIL import ImageDraw

def scale_dimensions(w, h, longest_side):
    if w > longest_side:
        ratio = longest_side*1./w
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

