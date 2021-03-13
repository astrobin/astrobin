# coding=utf-8

import sys
import os

DEFAULT_CHARSET = 'utf-8'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default.key').strip()
SITE_ID = 1

TESTING = os.environ.get("TESTING", 'false').strip() == 'true' or len(sys.argv) > 1 and sys.argv[1] == 'test'
DEBUG = os.environ.get('DEBUG', 'true').strip() == 'true'
INTERNAL_IPS = ['127.0.0.1', '172.18.0.1'] # localhost and docker gateway

MAINTENANCE_MODE = False
MAINTENANCE_LOCKFILE_PATH = 'maintenance-lock.file'

READONLY_MODE = os.environ.get("READONLY_MODE", 'false').strip() == 'true'
LONGPOLL_ENABLED = False

ALLOWED_HOSTS = ['*']
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760

ADS_ENABLED = os.environ.get('ADS_ENABLED', 'false').strip() == 'true'
ADSENSE_ENABLED = os.environ.get('ADSENSE_ENABLED', 'false').strip() == 'true'
DONATIONS_ENABLED = os.environ.get('DONATIONS_ENABLED', 'false').strip() == 'true'
PREMIUM_ENABLED = os.environ.get('PREMIUM_ENABLED', 'true').strip() == 'true'

BASE_URL = os.environ.get('BASE_URL', 'http://localhost').strip()
SHORT_BASE_URL = os.environ.get('SHORT_BASE_URL', BASE_URL).strip()
BASE_PATH = os.path.dirname(__file__)

MIN_INDEX_TO_LIKE = float(os.environ.get('MIN_INDEX_TO_LIKE', '1.00').strip())
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', 'invalid').strip()
GOOGLE_ADS_ID = os.environ.get('GOOGLE_ADS_ID', 'invalid').strip()

ROOT_URLCONF = 'astrobin.urls'

ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff')
ALLOWED_FITS_IMAGE_EXTENSIONS = ('xisf', 'fits', 'fit', 'fts')
ALLOWED_UNCOMPRESSED_SOURCE_EXTENSIONS = ALLOWED_FITS_IMAGE_EXTENSIONS + ('psd', 'tif', 'tiff')

GEOIP_PATH = os.path.abspath(os.path.dirname(__name__)) + "/astrobin/geoip2"

from django.utils.translation import ugettext_lazy as _

ALL_LANGUAGE_CHOICES = (
    ('ab', _(u'Abkhazian')),
    ('aa', _(u'Afar')),
    ('af', _(u'Afrikaans')),
    ('ak', _(u'Akan')),
    ('sq', _(u'Albanian')),
    ('am', _(u'Amharic')),
    ('ar', _(u'Arabic')),
    ('an', _(u'Aragonese')),
    ('hy', _(u'Armenian')),
    ('as', _(u'Assamese')),
    ('av', _(u'Avaric')),
    ('ae', _(u'Avestan')),
    ('ay', _(u'Aymara')),
    ('az', _(u'Azerbaijani')),
    ('bm', _(u'Bambara')),
    ('ba', _(u'Bashkir')),
    ('eu', _(u'Basque')),
    ('be', _(u'Belarusian')),
    ('bn', _(u'Bengali')),
    ('bh', _(u'Bihari languages')),
    ('bi', _(u'Bislama')),
    ('bs', _(u'Bosnian')),
    ('br', _(u'Breton')),
    ('bg', _(u'Bulgarian')),
    ('my', _(u'Burmese')),
    ('ca', _(u'Catalan / Valencian')),
    ('ch', _(u'Chamorro')),
    ('ce', _(u'Chechen')),
    ('ny', _(u'Chichewa, Chewa, Nyanja')),
    ('zh', _(u'Chinese')),
    ('cv', _(u'Chuvash')),
    ('kw', _(u'Cornish')),
    ('co', _(u'Corsican')),
    ('cr', _(u'Cree')),
    ('hr', _(u'Croatian')),
    ('cs', _(u'Czech')),
    ('da', _(u'Danish')),
    ('dv', _(u'Divehi  / Dhivehi / Maldivian')),
    ('nl', _(u'Dutch, Flemish')),
    ('dz', _(u'Dzongkha')),
    ('en', _(u'English')),
    ('eo', _(u'Esperanto')),
    ('et', _(u'Estonian')),
    ('ee', _(u'Ewe')),
    ('fo', _(u'Faroese')),
    ('fj', _(u'Fijian')),
    ('fi', _(u'Finnish')),
    ('fr', _(u'French')),
    ('ff', _(u'Fulah')),
    ('gl', _(u'Galician')),
    ('ka', _(u'Georgian')),
    ('de', _(u'German')),
    ('el', _(u'Greek')),
    ('gn', _(u'Guarani')),
    ('gu', _(u'Gujarati')),
    ('ht', _(u'Haitian / Haitian Creole')),
    ('ha', _(u'Hausa')),
    ('he', _(u'Hebrew')),
    ('hz', _(u'Herero')),
    ('hi', _(u'Hindi')),
    ('ho', _(u'Hiri Motu')),
    ('hu', _(u'Hungarian')),
    ('ia', _(u'Interlingua')),
    ('id', _(u'Indonesian')),
    ('ie', _(u'Interlingue / Occidental')),
    ('ga', _(u'Irish')),
    ('ig', _(u'Igbo')),
    ('ik', _(u'Inupiaq')),
    ('io', _(u'Ido')),
    ('is', _(u'Icelandic')),
    ('it', _(u'Italian')),
    ('iu', _(u'Inuktitut')),
    ('ja', _(u'Japanese')),
    ('jv', _(u'Javanese')),
    ('kl', _(u'Kalaallisut / Greenlandic')),
    ('kn', _(u'Kannada')),
    ('kr', _(u'Kanuri')),
    ('ks', _(u'Kashmiri')),
    ('kk', _(u'Kazakh')),
    ('km', _(u'Central Khmer')),
    ('ki', _(u'Kikuyu / Gikuyu')),
    ('rw', _(u'Kinyarwanda')),
    ('ky', _(u'Kirghiz / Kyrgyz')),
    ('kv', _(u'Komi')),
    ('kg', _(u'Kongo')),
    ('ko', _(u'Korean')),
    ('ku', _(u'Kurdish')),
    ('kj', _(u'Kuanyama / Kwanyama')),
    ('la', _(u'Latin')),
    ('lb', _(u'Luxembourgish, Letzeburgesch')),
    ('lg', _(u'Ganda')),
    ('li', _(u'Limburgan / Limburger / Limburgish')),
    ('ln', _(u'Lingala')),
    ('lo', _(u'Lao')),
    ('lt', _(u'Lithuanian')),
    ('lu', _(u'Luba / Katanga')),
    ('lv', _(u'Latvian')),
    ('gv', _(u'Manx')),
    ('mk', _(u'Macedonian')),
    ('mg', _(u'Malagasy')),
    ('ms', _(u'Malay')),
    ('ml', _(u'Malayalam')),
    ('mt', _(u'Maltese')),
    ('mi', _(u'Maori')),
    ('mr', _(u'Marathi')),
    ('mh', _(u'Marshallese')),
    ('mn', _(u'Mongolian')),
    ('na', _(u'Nauru')),
    ('nv', _(u'Navajo / Navaho')),
    ('nd', _(u'North Ndebele')),
    ('ne', _(u'Nepali')),
    ('ng', _(u'Ndonga')),
    ('nb', _(u'Norwegian Bokmål')),
    ('nn', _(u'Norwegian Nynorsk')),
    ('no', _(u'Norwegian')),
    ('ii', _(u'Sichuan Yi / Nuosu')),
    ('nr', _(u'South Ndebele')),
    ('oc', _(u'Occitan')),
    ('oj', _(u'Ojibwa')),
    ('cu', _(u'Church Slavic / Old Slavonic / Church Slavonic / Old Bulgarian / Old Church Slavonic')),
    ('om', _(u'Oromo')),
    ('or', _(u'Oriya')),
    ('os', _(u'Ossetian / Ossetic')),
    ('pa', _(u'Punjabi / Panjabi')),
    ('pi', _(u'Pali')),
    ('fa', _(u'Persian')),
    ('pl', _(u'Polish')),
    ('ps', _(u'Pashto / Pushto')),
    ('pt', _(u'Portuguese')),
    ('qu', _(u'Quechua')),
    ('rm', _(u'Romansh')),
    ('rn', _(u'Rundi')),
    ('ro', _(u'Romanian / Moldavian / Moldovan')),
    ('ru', _(u'Russian')),
    ('sa', _(u'Sanskrit')),
    ('sc', _(u'Sardinian')),
    ('sd', _(u'Sindhi')),
    ('se', _(u'Northern Sami')),
    ('sm', _(u'Samoan')),
    ('sg', _(u'Sango')),
    ('sr', _(u'Serbian')),
    ('gd', _(u'Gaelic / Scottish Gaelic')),
    ('sn', _(u'Shona')),
    ('si', _(u'Sinhala / Sinhalese')),
    ('sk', _(u'Slovak')),
    ('sl', _(u'Slovenian')),
    ('so', _(u'Somali')),
    ('st', _(u'Southern Sotho')),
    ('es', _(u'Spanish / Castilian')),
    ('su', _(u'Sundanese')),
    ('sw', _(u'Swahili')),
    ('ss', _(u'Swati')),
    ('sv', _(u'Swedish')),
    ('ta', _(u'Tamil')),
    ('te', _(u'Telugu')),
    ('tg', _(u'Tajik')),
    ('th', _(u'Thai')),
    ('ti', _(u'Tigrinya')),
    ('bo', _(u'Tibetan')),
    ('tk', _(u'Turkmen')),
    ('tl', _(u'Tagalog')),
    ('tn', _(u'Tswana')),
    ('to', _(u'Tonga')),
    ('tr', _(u'Turkish')),
    ('ts', _(u'Tsonga')),
    ('tt', _(u'Tatar')),
    ('tw', _(u'Twi')),
    ('ty', _(u'Tahitian')),
    ('ug', _(u'Uighur / Uyghur')),
    ('uk', _(u'Ukrainian')),
    ('ur', _(u'Urdu')),
    ('uz', _(u'Uzbek')),
    ('ve', _(u'Venda')),
    ('vi', _(u'Vietnamese')),
    ('vo', _(u'Volapük')),
    ('wa', _(u'Walloon')),
    ('cy', _(u'Welsh')),
    ('wo', _(u'Wolof')),
    ('fy', _(u'Western Frisian')),
    ('xh', _(u'Xhosa')),
    ('yi', _(u'Yiddish')),
    ('yo', _(u'Yoruba')),
    ('za', _(u'Zhuang / Chuang')),
    ('zu', _(u'Zulu')),
)
