# coding=utf-8

import sys
import os

DEFAULT_CHARSET = 'utf-8'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

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
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

ADS_ENABLED = os.environ.get('ADS_ENABLED', 'false').strip() == 'true'
DONATIONS_ENABLED = os.environ.get('DONATIONS_ENABLED', 'false').strip() == 'true'
PREMIUM_ENABLED = os.environ.get('PREMIUM_ENABLED', 'true').strip() == 'true'

APP_URL = os.environ.get('APP_URL', 'http://localhost:4400').strip()
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8083').strip()
SHORT_BASE_URL = os.environ.get('SHORT_BASE_URL', BASE_URL).strip()
BASE_PATH = os.path.dirname(__file__)

GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', 'invalid').strip()
GOOGLE_ADS_ID = os.environ.get('GOOGLE_ADS_ID', 'invalid').strip()

ROOT_URLCONF = 'astrobin.urls'

ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff')
ALLOWED_FITS_IMAGE_EXTENSIONS = ('xisf', 'fits', 'fit', 'fts')
ALLOWED_UNCOMPRESSED_SOURCE_EXTENSIONS = ALLOWED_FITS_IMAGE_EXTENSIONS + ('psd', 'tif', 'tiff')

GEOIP_PATH = os.path.abspath(os.path.dirname(__name__)) + "/astrobin/geoip2"

from django.utils.translation import ugettext_lazy as _

ALL_LANGUAGE_CHOICES = (
    ('ab', _('Abkhazian')),
    ('aa', _('Afar')),
    ('af', _('Afrikaans')),
    ('ak', _('Akan')),
    ('sq', _('Albanian')),
    ('am', _('Amharic')),
    ('ar', _('Arabic')),
    ('an', _('Aragonese')),
    ('hy', _('Armenian')),
    ('as', _('Assamese')),
    ('av', _('Avaric')),
    ('ae', _('Avestan')),
    ('ay', _('Aymara')),
    ('az', _('Azerbaijani')),
    ('bm', _('Bambara')),
    ('ba', _('Bashkir')),
    ('eu', _('Basque')),
    ('be', _('Belarusian')),
    ('bn', _('Bengali')),
    ('bh', _('Bihari languages')),
    ('bi', _('Bislama')),
    ('bs', _('Bosnian')),
    ('br', _('Breton')),
    ('bg', _('Bulgarian')),
    ('my', _('Burmese')),
    ('ca', _('Catalan / Valencian')),
    ('ch', _('Chamorro')),
    ('ce', _('Chechen')),
    ('ny', _('Chichewa, Chewa, Nyanja')),
    ('zh', _('Chinese')),
    ('cv', _('Chuvash')),
    ('kw', _('Cornish')),
    ('co', _('Corsican')),
    ('cr', _('Cree')),
    ('hr', _('Croatian')),
    ('cs', _('Czech')),
    ('da', _('Danish')),
    ('dv', _('Divehi  / Dhivehi / Maldivian')),
    ('nl', _('Dutch, Flemish')),
    ('dz', _('Dzongkha')),
    ('en', _('English')),
    ('eo', _('Esperanto')),
    ('et', _('Estonian')),
    ('ee', _('Ewe')),
    ('fo', _('Faroese')),
    ('fj', _('Fijian')),
    ('fi', _('Finnish')),
    ('fr', _('French')),
    ('ff', _('Fulah')),
    ('gl', _('Galician')),
    ('ka', _('Georgian')),
    ('de', _('German')),
    ('el', _('Greek')),
    ('gn', _('Guarani')),
    ('gu', _('Gujarati')),
    ('ht', _('Haitian / Haitian Creole')),
    ('ha', _('Hausa')),
    ('he', _('Hebrew')),
    ('hz', _('Herero')),
    ('hi', _('Hindi')),
    ('ho', _('Hiri Motu')),
    ('hu', _('Hungarian')),
    ('ia', _('Interlingua')),
    ('id', _('Indonesian')),
    ('ie', _('Interlingue / Occidental')),
    ('ga', _('Irish')),
    ('ig', _('Igbo')),
    ('ik', _('Inupiaq')),
    ('io', _('Ido')),
    ('is', _('Icelandic')),
    ('it', _('Italian')),
    ('iu', _('Inuktitut')),
    ('ja', _('Japanese')),
    ('jv', _('Javanese')),
    ('kl', _('Kalaallisut / Greenlandic')),
    ('kn', _('Kannada')),
    ('kr', _('Kanuri')),
    ('ks', _('Kashmiri')),
    ('kk', _('Kazakh')),
    ('km', _('Central Khmer')),
    ('ki', _('Kikuyu / Gikuyu')),
    ('rw', _('Kinyarwanda')),
    ('ky', _('Kirghiz / Kyrgyz')),
    ('kv', _('Komi')),
    ('kg', _('Kongo')),
    ('ko', _('Korean')),
    ('ku', _('Kurdish')),
    ('kj', _('Kuanyama / Kwanyama')),
    ('la', _('Latin')),
    ('lb', _('Luxembourgish, Letzeburgesch')),
    ('lg', _('Ganda')),
    ('li', _('Limburgan / Limburger / Limburgish')),
    ('ln', _('Lingala')),
    ('lo', _('Lao')),
    ('lt', _('Lithuanian')),
    ('lu', _('Luba / Katanga')),
    ('lv', _('Latvian')),
    ('gv', _('Manx')),
    ('mk', _('Macedonian')),
    ('mg', _('Malagasy')),
    ('ms', _('Malay')),
    ('ml', _('Malayalam')),
    ('mt', _('Maltese')),
    ('mi', _('Maori')),
    ('mr', _('Marathi')),
    ('mh', _('Marshallese')),
    ('mn', _('Mongolian')),
    # The 'mo' language code is actually removed from the ISO standard but we keep it here due to reasons of political
    # tension.
    ('mo', _('Moldavian / Moldovan')),
    ('na', _('Nauru')),
    ('nv', _('Navajo / Navaho')),
    ('nd', _('North Ndebele')),
    ('ne', _('Nepali')),
    ('ng', _('Ndonga')),
    ('nb', _('Norwegian Bokmål')),
    ('nn', _('Norwegian Nynorsk')),
    ('no', _('Norwegian')),
    ('ii', _('Sichuan Yi / Nuosu')),
    ('nr', _('South Ndebele')),
    ('oc', _('Occitan')),
    ('oj', _('Ojibwa')),
    ('cu', _('Church Slavic / Old Slavonic / Church Slavonic / Old Bulgarian / Old Church Slavonic')),
    ('om', _('Oromo')),
    ('or', _('Oriya')),
    ('os', _('Ossetian / Ossetic')),
    ('pa', _('Punjabi / Panjabi')),
    ('pi', _('Pali')),
    ('fa', _('Persian')),
    ('pl', _('Polish')),
    ('ps', _('Pashto / Pushto')),
    ('pt', _('Portuguese')),
    ('qu', _('Quechua')),
    ('rm', _('Romansh')),
    ('rn', _('Rundi')),
    ('ro', _('Romanian')),
    ('ru', _('Russian')),
    ('sa', _('Sanskrit')),
    ('sc', _('Sardinian')),
    ('sd', _('Sindhi')),
    ('se', _('Northern Sami')),
    ('sm', _('Samoan')),
    ('sg', _('Sango')),
    ('sr', _('Serbian')),
    ('gd', _('Gaelic / Scottish Gaelic')),
    ('sn', _('Shona')),
    ('si', _('Sinhala / Sinhalese')),
    ('sk', _('Slovak')),
    ('sl', _('Slovenian')),
    ('so', _('Somali')),
    ('st', _('Southern Sotho')),
    ('es', _('Spanish / Castilian')),
    ('su', _('Sundanese')),
    ('sw', _('Swahili')),
    ('ss', _('Swati')),
    ('sv', _('Swedish')),
    ('ta', _('Tamil')),
    ('te', _('Telugu')),
    ('tg', _('Tajik')),
    ('th', _('Thai')),
    ('ti', _('Tigrinya')),
    ('bo', _('Tibetan')),
    ('tk', _('Turkmen')),
    ('tl', _('Tagalog')),
    ('tn', _('Tswana')),
    ('to', _('Tonga')),
    ('tr', _('Turkish')),
    ('ts', _('Tsonga')),
    ('tt', _('Tatar')),
    ('tw', _('Twi')),
    ('ty', _('Tahitian')),
    ('ug', _('Uighur / Uyghur')),
    ('uk', _('Ukrainian')),
    ('ur', _('Urdu')),
    ('uz', _('Uzbek')),
    ('ve', _('Venda')),
    ('vi', _('Vietnamese')),
    ('vo', _('Volapük')),
    ('wa', _('Walloon')),
    ('cy', _('Welsh')),
    ('wo', _('Wolof')),
    ('fy', _('Western Frisian')),
    ('xh', _('Xhosa')),
    ('yi', _('Yiddish')),
    ('yo', _('Yoruba')),
    ('za', _('Zhuang / Chuang')),
    ('zu', _('Zulu')),
)

# Automatically approve content from users with email addresses in the following domains.
AUTO_APPROVE_DOMAINS = (
    '@astrobin.com',
    '@highpointscientific.com',
)
