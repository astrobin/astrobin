# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'
LANGUAGE_COOKIE_NAME = 'astrobin_lang'

gettext = lambda s: s
LANGUAGES = (
    ('en', gettext('English (US)')),
    ('en-GB', gettext('English (GB)')),
    ('it', gettext('Italian')),
    ('es', gettext('Spanish')),
    ('fr', gettext('French')),
    ('fi', gettext('Finnish')),
    ('de', gettext('German')),
    ('nl', gettext('Dutch')),
    ('tr', gettext('Turkish')),
    ('sq', gettext('Albanian')),
    ('pl', gettext('Polish')),
    ('pt', gettext('Portuguese')),
    ('el', gettext('Greek')),
    ('ru', gettext('Russian')),
    ('ar', gettext('Arabic')),
    ('ja', gettext('Japanese')),
)
MODELTRANSLATION_TRANSLATION_REGISTRY = 'astrobin.translation'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

