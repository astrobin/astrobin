from astrobin.models import Telescope, Camera, Software, Filter, Mount, Accessory, FocalReducer

TYPES_LOOKUP = {
    'Telescope': Telescope.TELESCOPE_TYPES,
    'Camera': Camera.CAMERA_TYPES,
    'Software': Software.SOFTWARE_TYPES,
    'Filter': Filter.FILTER_TYPES,
}

CLASS_LOOKUP = {
    'Telescope': Telescope,
    'Camera': Camera,
    'Mount': Mount,
    'Filter': Filter,
    'Software': Software,
    'Accessory': Accessory,
    'FocalReducer': FocalReducer,
}

def get_correct_gear(id):
    types = (
        Telescope,
        Mount,
        Camera,
        FocalReducer,
        Software,
        Filter,
        Accessory,
    )
    gear = None
    gear_type = None
    for type in types:
        try:
            gear = type.objects.get(id = id)
            gear_type = gear.__class__.__name__
            return (gear, gear_type)
        except type.DoesNotExist:
            continue

    return (None, None)


def is_gear_complete(id):
    gear, gear_type = get_correct_gear(id)
    
    ret = False
    if gear_type == 'Telescope':
        ret = (gear.aperture != None and
               gear.focal_length != None and
               gear.type != None)
    elif gear_type == 'Mount':
        ret = (gear.max_payload != None and
               gear.pe != None)
    elif gear_type == 'Camera':
        ret = (gear.pixel_size != None and
               gear.sensor_width != None and
               gear.sensor_height != None and
               gear.type != None)
    elif gear_type == 'FocalReducer':
        ret = True
    elif gear_type == 'Software':
        ret = (gear.type != None)
    elif gear_type == 'Filter':
        ret = (gear.type != None and
               gear.bandwidth != None)
    elif gear_type == 'Accessory':
        ret = True

    ret = ret and (gear.make != None) and (gear.make != '')
    return ret


