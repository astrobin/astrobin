from modeltranslation.translator import translator, TranslationOptions
from astrobin.models import CommercialGear

class CommercialGearTranslationOptions(TranslationOptions):
    fields = ('tagline', 'description',)

translator.register(CommercialGear, CommercialGearTranslationOptions)