import logging
import re
from typing import List, Optional

import bleach
import requests
from django.conf import settings
from lingua import Language, LanguageDetectorBuilder
from langdetect import detect as langdetect_detect, LangDetectException
from requests.adapters import HTTPAdapter
from urllib3 import Retry

logger = logging.getLogger('astrobin')

# Map Django language codes to Lingua Language enum
# The mapping isn't always 1:1, so we need to handle some special cases
DJANGO_TO_LINGUA_LANG_MAP = {
    'en': Language.ENGLISH,
    'en-GB': Language.ENGLISH,  # Lingua doesn't distinguish between US/GB English
    'it': Language.ITALIAN,
    'es': Language.SPANISH,
    'fr': Language.FRENCH,
    'fi': Language.FINNISH,
    'de': Language.GERMAN,
    'nl': Language.DUTCH,
    'tr': Language.TURKISH,
    'sq': Language.ALBANIAN,
    'pl': Language.POLISH,
    'pt': Language.PORTUGUESE,
    'el': Language.GREEK,
    'uk': Language.UKRAINIAN,
    'ru': Language.RUSSIAN,
    'ja': Language.JAPANESE,
    'zh-hans': Language.CHINESE,  # Simplified Chinese
    'hu': Language.HUNGARIAN,
    'be': Language.BELARUSIAN,
    'sv': Language.SWEDISH,
}


# Global detector instance that will be initialized at application startup
_LANGUAGE_DETECTOR = None

def build_lingua_detector():
    """
    Builds and returns a new language detector.
    This is called once during application startup via AppConfig.ready()
    """
    global _LANGUAGE_DETECTOR
    import time
    start_time = time.time()
    
    # Get supported languages from settings if available, or use default set
    try:
        supported_lang_codes = [code for code, name in settings.LANGUAGES]
        lingua_languages = [
            DJANGO_TO_LINGUA_LANG_MAP.get(code) for code in supported_lang_codes
            if code in DJANGO_TO_LINGUA_LANG_MAP
        ]
        # Filter out None values
        lingua_languages = [lang for lang in lingua_languages if lang is not None]
        
        if not lingua_languages:  # Fallback if we couldn't map any languages
            lingua_languages = [Language.ENGLISH]
            logger.warning("Couldn't map any Django languages to Lingua. Using English only.")
    except (ImportError, AttributeError):
        # Fallback to common languages if settings are not available
        lingua_languages = [
            Language.ENGLISH, Language.SPANISH, Language.FRENCH, Language.GERMAN,
            Language.ITALIAN, Language.PORTUGUESE, Language.CHINESE
        ]
        logger.warning("Could not load languages from Django settings. Using default set.")

    # Build the detector
    logger.info(f"Initializing Lingua language detector with {len(lingua_languages)} languages")
    if getattr(settings, 'DEBUG', False):
        logger.debug(
            f"Languages: {', '.join([lang.name for lang in lingua_languages])}"
        )
    
    detector = LanguageDetectorBuilder.from_languages(*lingua_languages)\
        .with_preloaded_language_models()\
        .with_low_accuracy_mode()\
        .build()
    
    initialization_time = time.time() - start_time
    logger.info(f"Lingua language detector initialized in {initialization_time:.2f} seconds")
    
    _LANGUAGE_DETECTOR = detector
    return detector


# Function to get the detector instance
def get_language_detector():
    """
    Returns the global detector instance. This should always be initialized
    during application startup, but includes a fallback just in case.
    """
    global _LANGUAGE_DETECTOR
    if _LANGUAGE_DETECTOR is None:
        logger.warning("Lingua detector not initialized at startup; initializing now")
        return build_lingua_detector()
    return _LANGUAGE_DETECTOR


class UtilsService:
    @staticmethod
    def http_with_retries(
            url: str, method='GET', headers=None, verify=True, allow_redirects=True, stream=False, **kwargs
    ) -> requests.Response:
        retry_strategy: Retry = Retry(total=3, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1)
        adapter: HTTPAdapter = HTTPAdapter(max_retries=retry_strategy)
        session: requests.Session = requests.Session()

        session.mount('https://', adapter)
        session.mount('http://', adapter)

        return session.request(
            method=method,
            url=url,
            headers=headers,
            verify=verify,
            allow_redirects=allow_redirects,
            stream=stream,
            **kwargs
        )

    @staticmethod
    def unique(sequence):
        # Return unique items preserving order.
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    @staticmethod
    def split_text_alphanumerically(s: str) -> List[str]:
        return re.findall(r"[^\W\d_]+|\d+", s)

    @staticmethod
    def anonymize_email(email):
        username, domain = email.split('@')

        if len(username) <= 2:
            username = '*' * len(username)
        else:
            username = f"{username[0]}****{username[-1]}"

        return f"{username}@{domain}"

    @staticmethod
    def get_search_synonyms_text(text: str) -> Optional[str]:
        data = """
messier 1,sharpless 244,taurus a,crab nebula,crab neb,crab,sh 2 244,ngc 1952,m 1
m 2,ngc 7089,gcl 121,messier 2
gcl 25,ngc 5272,messier 3,m 3
m 4,spider globular,messier 4,ngc 6121,gcl 41
messier 5,gcl 34,ngc 5904,rose cluster,m 5
ngc 6405,butterfly cluster,m 6,messier 6
messier 7,ngc 6475,ptolemy's cluster,m 7
rcw 146,sharpless 25,messier 8,sh 2 25,ngc 6523,m 8,gum 72,lagoon nebula
messier 9,ngc 6333,gcl 60,m 9
messier 10,m 10,ngc 6254
messier 11,ngc 6705,wild duck cluster,m 11
messier 12,ngc 6218,m 12
ngc 6205,messier 13,hercules globular cluster,great hercules cluster,m 13
messier 14,gcl 72,ngc 6402,m 14
gcl 120,m 15,messier 15,ngc 7078,great pegasus cluster
sharpless 49,eagle nebula,ocl 54,messier 16,ic 4703,gum 83,ngc 6611,m 16,sh 2 49,star queen,lbn 67
sharpless 45,ngc 6618,lbn 60,sh 2 45,lobster nebula,messier 17,swan nebula,omega swan horseshoe lobster or checkmark nebula,gum 81,m 17,checkmark nebula,horseshoe nebula,omega nebula
messier 18,black swan cluster,ngc 6613,m 18
gcl 52,messier 19,m 19,ngc 6273
trifid nebula,sharpless 30,m 20,messier 20,sh 2 30,ngc 6514,gum 76
ngc 6531,m 21,messier 21
messier 22,great sagittarius cluster,ngc 6656,m 22
messier 23,ngc 6494,m 23
ic 4715,m 24,small sagittarius star cloud,messier 24
m 25,ic 4725,messier 25
ngc 6694,messier 26,m 26
m 27,diabolo nebula,messier 27,ngc 6853,dumbbell nebula
gcl 94,messier 28,m 28,ngc 6626
messier 29,ngc 6913,cooling tower,m 29
m 30,messier 30,gcl 122,ngc 7099,jellyfish cluster
andromeda galaxy,messier 31,andromeda,m 31,andromeda nebula,and nebula,ngc 224,ugc 454
messier 32,m 32,andromeda satellite 1,ngc 221,galaxy 8
ngc 598,m 33,triangulum pinwheel,triangulum pinwheel galaxy,triangulum galaxy,messier 33
messier 34,m 34,spiral cluster,ocl 382,ngc 1039
m 35,shoe buckle cluster,messier 35,ngc 2168
ngc 1960,ocl 445,messier 36,pinwheel cluster,m 36
ngc 2099,salt and pepper cluster,messier 37,m 37
ngc 1912,m 38,starfish cluster,messier 38
messier 39,ngc 7092,m 39
m 40,winnecke 4,messier 40
ngc 2287,little beehive cluster,m 41,messier 41
orion nebula,messier 42,sh 2 281,ori nebula,m 42,ngc 1976,sharpless 281,great orion nebula
mairan's nebula,messier 43,ngc 1982,de mairan's nebula,m 43
ngc 2632,m 44,praesepe,messier 44,praesepe cluster,beehive,beehive cluster,beehive cluster or praesepe
pleiades,m 45,messier 45,subaru,seven sisters
messier 46,ngc 2437,m 46
m 47,messier 47,ngc 2422
ngc 2548,m 48,messier 48
ngc 4472,m 49,messier 49
messier 50,heart shaped cluster,ngc 2323,m 50
question mark galaxy,whirlpool galaxy,ngc 5194 ngc 5195,whirlpool,m 51,ngc 5194,messier 51
scorpion cluster,m 52,ocl 260,messier 52,ngc 7654
messier 53,gcl 22,m 53,ngc 5024
messier 54,m 54,ngc 6715,gcl 104
gcl 113,messier 55,m 55,ngc 6809
m 56,messier 56,ngc 6779,gcl 110
messier 57,ring nebula,ngc 6720,m 57
ngc 4579,m 58,messier 58
ngc 4621,messier 59,v 17,m 59
ngc 4649,v 19,messier 60,m 60
messier 61,m 61,ngc 4303,swelling spiral
messier 62,flickering globular,gcl 51,ngc 6266,m 62
m 63,sunflower galaxy,ngc 5055,messier 63,ugc 8334
m 64,messier 64,ngc 4826,evil eye galaxy,black eye galaxy
ngc 3627,m 65,leo triplet,ngc 3623,m 66,messier 66,messier 65
king cobra cluster,m 67,messier 67,ngc 2682
m 68,gcl 20,messier 68,ngc 4590
ngc 6637,gcl 96,messier 69,m 69
m 70,messier 70,ngc 6681,gcl 101
messier 71,m 71,ngc 6838,angelfish cluster,gcl 115
ngc 6981,gcl 118,messier 72,m 72
m 73,messier 73,ngc 6994,ocl 89
ngc 628,m 74,messier 74
ngc 6864,gcl 116,messier 75,m 75
little dumbbell nebula,cork nebula,ngc 650,messier 76,m 76,barbell nebula,ngc 651
messier 77,ngc 1068,m 77,squid galaxy,cetus a galaxy
casper the friendly ghost nebula,ngc 2068,m 78,messier 78
ngc 1904,m 79,messier 79
gcl 39,m 80,ngc 6093,messier 80
ngc 3031,m 81,messier 81,bode's galaxy
ngc 3034,messier 82,m 82,uma a,cigar galaxy
southern pinwheel galaxy,m 83,ngc 5236,messier 83
ngc 4374,messier 84,m 84
messier 85,m 85,ngc 4382
m 86,ngc 4406,messier 86
m 87,messier 87,smoking gun galaxy,virgo a,virgo galaxy,virgo a galaxy,ngc 4486,smoking gun
ngc 4501,m 88,messier 88
ngc 4552,m 89,messier 89
messier 90,ngc 4569,m 90
ngc 4548,messier 91,m 91
messier 92,ngc 6341,m 92,gcl 59
m 93,ngc 2447,messier 93
crocodile eye galaxy,cat's eye galaxy,ngc 4736,m 94,messier 94
ngc 3351,m 95,messier 95
leo 19,messier 96,m 96,ngc 3368
owl nebula,messier 97,m 97,ngc 3587
ngc 4192,m 98,messier 98
messier 99,coma pinwheel,st catherine s wheel,m 99,ngc 4254,virgo cluster pinwheel
mirror galaxy,m 100,messier 100,ngc 4321,h 23
messier 101,pinwheel galaxy,pinwheel,ngc 5457,m 101
ngc 5866,ngc 3115,messier 102,m 102,spindle galaxy,caldwell 53,c 53
ocl 326,m 103,ngc 581,messier 103
sombrero,m 104,messier 104,ngc 4594,sombrero galaxy
m 105,leo 2,ngc 3379,messier 105
m 106,messier 106,ngc 4258,ugc 7353
crucifix cluster,ngc 6171,m 107,gcl 44,messier 107
ngc 3556,surfboard galaxy,messier 108,m 108
m 109,vacuum cleaner galaxy,messier 109,ngc 3992
leda 2429,m 110,messier 110,galaxy 7,ugc 426,ngc 205
caldwell 1,c 1,ngc 188
c 10,caldwell 10,ocl 333,ngc 663
gum 42,ic 2944,rcw 62,c 100,lam cen nebula,caldwell 100
c 101,caldwell 101,ngc 6744
caldwell 16,ic 2602,c 102,ngc 4884,ngc 4889,s 56,caldwell 35,c 16,ngc 7243,caldwell 102,c 35,ngc 4839
tarantula,c 103,caldwell 103,ngc 2070
gcl 3,ngc 362,c 104,caldwell 104
ngc 4833,c 105,caldwell 105,gcl 21
gcl 1,c 106,ngc 104,caldwell 106
gcl 40,caldwell 107,c 107,ngc 6101
c 108,gcl 19,ngc 4372,caldwell 108
c 109,ngc 3195,caldwell 109
ngc 7635,bubble nebula,lbn 548,sharpless 162,sh 2 162
caldwell 12,ugc 11597,ngc 6946,c 12,ngc 4872
owl cluster,c 13,et cluster,ocl 321,ngc 457,caldwell 13
h persei cluster,ngc 869,ocl 353,chi persei cluster,ocl 350,ngc 884
ngc 6826,caldwell 15,c 15,blinking planetary
ngc 147,caldwell 17,ic 4011,c 17
c 18,ngc 185,caldwell 18
ic 5146,c 19,cocoon nebula,sh 2 125,lbn 424,sharpless 125,caldwell 19
north america,ngc 7000,sh 2 117,caldwell 20,lbn 373,sharpless 117,c 20,north america nebula
caldwell 21,c 21,ngc 4449
caldwell 22,ngc 7662,c 22,copeland's blue snowball
ngc 1275,per a,perseus a
caldwell 26,c 26,ngc 4244
sh 2 105,ngc 6888,ngc 4881,sharpless 105,crescent nebula,c 27,lbn 203,caldwell 27
caldwell 28,c 28,ngc 752,ocl 363
ugc 12113,ngc 7331,caldwell 30,c 30
flaming star nebula,ic 405,c 31,lbn 795,caldwell 31,sharpless 229,sh 2 229
caldwell 32,ngc 4631,n 4631,whale galaxy,c 32
ngc 6992,caldwell 33,c 33
veil nebula,caldwell 34,c 34,ngc 6960,filamentary nebula,lbn 191,cirrus nebula
ngc 4559,c 36,caldwell 36
ngc 4565,caldwell 38,ugc 7772,c 38
eskimo nebula,caldwell 39,c 39,ngc 2392,clown nebula
ocl 235,c 4,ngc 7023,lbn 487,caldwell 4,iris nebula
hrs 46,ngc 3626
mel 25,caldwell 41,c 41
c 43,ngc 7814,ugc 8,caldwell 43
c 44,caldwell 44,ngc 7479
caldwell 45,ngc 5248,c 45
caldwell 46,ngc 2261,c 46,lbn 920,hubble's nebula
ngc 6934,gcl 117,c 47,caldwell 47
caldwell 48,c 48,ngc 2775
ngc 2244 satellite cluster,ngc 2237,c 49,caldwell 49,rosette a
ugc 2847,ic 342
caldwell 50,ngc 2244,ngc 2239,c 50
ic 1613,c 51,caldwell 51
ngc 2506,caldwell 54,c 54
ngc 7009,saturn nebula,c 55,caldwell 55
pk 118 74 1,ngc 246,c 56,caldwell 56
barnard's galaxy,caldwell 57,c 57,ic 4895,ngc 6822
caldwell 58,c 58,ngc 2360,caroline's cluster
ngc 3242,caldwell 59,jupiter's ghost nebula,c 59,ghost of jupiter
sunflower nebula,ngc 6543,cat's eye nebula
c 60,caldwell 60,ngc 4038
eso 572 48,c 61,caldwell 61,ngc 4039
caldwell 62,ngc 247,c 62
ngc 7293,c 63,helix nebula,caldwell 63
tau cma,caldwell 64,ngc 2362,c 64
caldwell 65,ngc 253,silver coin,sculptor filament,c 65
c 66,caldwell 66,ngc 5694
ic 3583,ugc 5079,ngc 1097,caldwell 67,c 67,ngc 2905,ngc 2903
ngc 6729,caldwell 68,c 68
ngc 6337,ngc 6302,sh 2 6,bug nebula,pk 349 01 1,c 69,butterfly nebula,sharpless 6,caldwell 69
c 7,ugc 3918,caldwell 7,ngc 2403
am 0052 375,caldwell 70,ngc 300,c 70
ngc 2477,c 71,caldwell 71
c 72,ngc 55,caldwell 72
c 73,gcl 9,caldwell 73,ngc 1851
c 74,caldwell 74,ngc 3132,eight burst nebula
c 75,ngc 6124,caldwell 75
ngc 6231,caldwell 76,c 76
c 77,ngc 5128,caldwell 77,cen a,centaurus a
ngc 6541,caldwell 78,c 78,gcl 86
gcl 15,caldwell 79,ngc 3201,c 79
ngc 6352,caldwell 81,gcl 64,c 81
caldwell 82,ngc 6193,c 82
c 83,caldwell 83,ngc 4945
caldwell 84,c 84,gcl 26,ngc 5286
ic 2391,caldwell 85,c 85
ngc 6397,gcl 74,caldwell 86,c 86
c 87,caldwell 87,gcl 5,ngc 1261
ngc 5823,caldwell 88,c 88
caldwell 89,ocl 948,ngc 6087,c 89
sharpless 155,caldwell 9,sh 2 155,cave nebula
ngc 3532,c 91,caldwell 91
ngc 3372,c 92,caldwell 92,carina nebula,rcw 53,keyhole,car nebula,keyhole nebula,eta car nebula
caldwell 93,gcl 108,c 93,ngc 6752
jewel box,herschel's jewel box,caldwell 94,kappa crucis cluster,c 94,ngc 4755
caldwell 95,ngc 6025,c 95
caldwell 96,ngc 2516,c 96
ngc 3766,caldwell 97,c 97
c 98,caldwell 98,ngc 4609
caldwell 99,c 99
wr 40,hd 96548,rcw 58
messier 82 15,m 82 15
wr 134,v 1769 cyg,hip 99377,hd 191765,sao 69541
wr 136,hip 99546
v 1679 cyg,wr 137
v 444 cyg,wr 139
hd 193793,hip 100287,wr 140
sh 2 8,ngc 6334,sharpless 8,gum 64,gum 62,cat's paw nebula,rcw 127
the war and peace nebula,gum 66,sh 2 11,ngc 6357,sharpless 11,war and peace nebula
sharpless 29,sh 2 29
rcw 174,sh 2 64,sharpless 64,w 40
sh 2 101,sharpless 101,cygnus star cloud,tulip nebula
celestial snow angel,sharpless 106,sh 2 106
sharpless 140,sh 2 140
ngc 7538,sharpless 158,sh 2 158
sh 2 171,sharpless 171,lbn 589,ngc 7822
sharpless 184,lbn 616,sh 2 184,ic 11,ngc 281,ngc 281 w
sharpless 191,maffei 1,sh 2 191,pgc 9892
maffei 2,sharpless 197,sh 2 197
soul nebula,sharpless 199,ic 1848,sh 2 199,lbn 667
sharpless 212,sharpless 211,sh 2 212,ngc 1624,sh 2 211
sharpless 220,california nebula,lbn 756,sh 2 220,ngc 1499
sh 2 237,ngc 1931,sharpless 237
sh 2 238,hind's variable nebula,hind's nebula,ngc 1555,sharpless 238
sharpless 248,ic 443,sh 2 248,jellyfish nebula,gem a,lbn 844
rosette nebula,sh 2 275,sharpless 275
ngc 1975,sh 2 279,ngc 1977,the running man nebula,running man nebula,sharpless 279,ngc 1973
barnard's loop,sh 2 276,sharpless 276
sharpless 277,sh 2 271,ngc 2024,sharpless 271,flame nebula,sh 2 277
sharpless 297,lbn 1039,ced 90,sh 2 297
sh 2 298,lbn 1041,sharpless 298,ngc 2359,rcw 5,thor's helmet,gum 4
gum 12,gum nebula
rcw 32,gum 15
vela supernova remnant,gum 16
rcw 36,gum 20
gum 29,rcw 49
ngc 6550,ngc 6548
ngc 4228,ngc 4214
ngc 6820,ngc 4636
mrk 86,ngc 2537,bear paw galaxy,bear's paw,bear claw nebula
ngc 3928,miniature spiral
ngc 4170,ngc 4173
hrs 37,ngc 3512
lbn 1067,gum 9,sh 2 311,rcw 16,sharpless 311,ngc 2467
ocl 452,ngc 1746
ocl 99,ngc 6756
ngc 6474,ngc 6473
ngc 6603,ocl 36
ngc 3144,ngc 3174
ngc 1360,pk 220 53 1
galaxy 85,ngc 1272,p 17
ngc 6331,galaxy c
ngc 1331,ic 324
sh 2 206,lbn 704,sharpless 206,ngc 1491
eso 358 13,ngc 1350
galaxy 338,ngc 5044
ngc 4395,ugc 7524
aco 2593,ngc 7649
ngc 1991,ngc 1974
ocl 68,ngc 6664
kpg 265,ngc 3509
ngc 5822,ocl 937
ngc 5375,ngc 5396
ngc 6293,gcl 55
monkey head nebula,ngc 2174
ngc 5953,ngc 5954
ngc 2936,ugc 5130
aco 262,ngc 704,ngc 708,galaxy 55,ngc 705
gcl 93,ngc 6624
ngc 1316,fornax a
ngc 2282,vdb 85
ngc 680,galaxy 50
ngc 17,ngc 34
sharpless 222,sh 2 222,ngc 1579
galaxy 30,ngc 501
ugc 6524,ngc 3718
ocl 280,ngc 7762
galaxy 400,ngc 6482
ngc 1893,ocl 439
hrs 55,ngc 3684
ngc 1566,eso 157 20
ngc 70,ic 1539
gcl 125,ngc 7492
ngc 6388,gcl 70
hrs 24,ngc 3430
gum 38 b,ngc 3603
ngc 5364,ngc 5317
ngc 5634,gcl 28
ngc 6584,gcl 92
ocl 357,ngc 1027
vv 199,ngc 4211
ocl 134,ngc 6834
ngc 6652,gcl 98
ngc 736,galaxy 60
pk 069 02 1,ngc 6894
ngc 1367,ngc 1371
ngc 6544,gcl 87
b 08,ngc 909
hrs 43,ngc 3608
ngc 145,sm 5
ngc 3180,ngc 3184
hrs 3,ngc 3226
box nebula,ngc 6309
virgo 3,ngc 4438
ngc 4413,ngc 4407
b 11,ngc 912
ocl 320,ngc 436
ngc 4323,ngc 4322
ic 2126,ngc 1935
ngc 3395,hrs 20
ngc 4103,ocl 871
maia nebula,ngc 1432
ngc 1049,for 3,fornax 3
ngc 6760,gcl 109
vdb 119,ngc 6590,sharpless 37,sh 2 37,lbn 46
ngc 3373,ngc 3389
mon r 2 irs 3,ngc 2170
leo 3,ngc 3377
ocl 462,ngc 1807
ngc 3994,ngc 3995
ngc 4565 a,ngc 4562
eso 499 36,ngc 3109
ic 1178,ngc 3222
rcw 48,gum 28,ngc 3199
ngc 6649,ocl 66
ngc 529,galaxy 33
ngc 2793,lt 6
ngc 7253 a,ngc 7253
gcl 56,ngc 6304
ngc 3455,hrs 30
ngc 6905,blue flash nebula
little gem,ngc 6445
ngc 1961,ic 2133
ngc 6847,sh 2 97,sharpless 97
ngc 6188,rim nebula
galaxy 115,ngc 1549
gcl 91,ngc 6569
ngc 4156,a 140
ngc 4437,ngc 4517
ocl 434,ngc 1907
ugc 8307,ngc 5033
gcl 48,ngc 6235
ngc 5982,galaxy 384
ngc 697,ngc 674
galaxy 27,ngc 410
ngc 5617,ocl 919
a 54,ngc 6041
ngc 3861 a,vv 3,ngc 3842,ngc 3861,aco 1367 2,galaxy 16,e 25,ic 701
hd 148937,gum 52,ngc 6164,ngc 6165
ngc 2874,ngc 2872
ced 16,lbn 741,ngc 1333
galaxy 100,ngc 1399
foxhead cluster,ngc 6819
polarissima australis,ngc 2573
galaxy 29,ngc 499
ngc 3681,hrs 54
ngc 1291,ngc 1269
st 2,ngc 1936
ngc 6356,gcl 62
ocl 945,ngc 6005
ocl 575,ngc 2345
ngc 507,galaxy 31
ugc 11681,ngc 7025
gum 30,ngc 3293
ugc 7907,ngc 4656
wray 16 47,ngc 2899
ngc 5390,ngc 5371
gum 47,ic 4274,ngc 5189
ngc 895,ngc 894
gcl 78,ngc 6441
gcl 103,ngc 6712
ngc 7140,ngc 7141
ocl 991,ngc 6250
ngc 654,ocl 330
ngc 6727,ngc 6726
ic 5136,ngc 7135
p 12,ngc 1270
ngc 6951,ngc 6952
ngc 5466,gcl 27
ngc 541,galaxy 35,ngc 547
ngc 5204,sm 90
ugc 7118,ngc 4125
ngc 3683,hrs 56
ngc 3510,sm 60
little ghost nebula,ngc 6369
ngc 4208,ngc 4212
ngc 7252,atoms for peace galaxy
ngc 2509,ocl 630
kite cluster,ngc 6866
gcl 89,ngc 6558
ngc 2727,ngc 2708
am 1026 442,ngc 3261
ngc 2579,gum 11
ngc 2163,lbn 855
helix galaxy,ngc 2685
ugc 7282,ngc 4217
ngc 7021,ngc 7020
ngc 4473,v 10
ngc 1435,merope nebula
ngc 2443,ngc 2442
ocl 1001,ngc 6242
galaxy 26,ngc 404
galaxy 3,ngc 83,s 03
ngc 5907,ngc 5906
ngc 4443,virgo 4,ngc 4461
ngc 1909,the witch head nebula,ic 2118
a 14,ngc 6166
ngc 6842,sh 2 95,sharpless 95
ngc 2421,ocl 626
ocl 468,ngc 2158
nubecula minor,small magellanic cloud,ngc 292,smc
b 26,b 27,ngc 4657
ocl 928,ngc 5662
umbrella galaxy,ngc 4651
ngc 4346,s 15
ngc 3804,ngc 3794
b 10,ngc 911
ngc 1317,ngc 1318
s 02,ngc 85
ngc 6723,gcl 106
hrs 57,ngc 3686
ngc 7578,hcg 94 a
ngc 5278,g 22
ngc 6284,gcl 53
eso 358 17,ngc 1365
p 36,ngc 1293
ngc 6496,gcl 80
ngc 6040,a 45
ngc 380,galaxy 18
ngc 7130,ic 5135
ngc 379,galaxy 17
ngc 5458,h 22
gcl 65,ngc 6366
ngc 1404,galaxy 102
ngc 2736,rcw 37,pencil nebula
ngc 6067,ocl 953
ngc 2372,ngc 2371 2,ngc 2371
nuclear,ngc 5930
ngc 1748,ic 2114
gcl 36,ngc 5946
ngc 2022,pk 196 10 1
ugc 6350,ngc 3628
ngc 3189,ngc 3190
leo 1,ngc 3371,ngc 3384
ngc 6830,ocl 125
ugc 4966,ngc 2841
galaxy 20,ngc 383
ngc 5986,gcl 37
a 10,ngc 7437
ngc 6539,gcl 85
gcl 66,ngc 6362
gum 38 a,ngc 3576
ngc 2246,rosette b
red spider nebula,ngc 6537
galaxy 2,s 04,ngc 80
ngc 6741,phantom streak nebula
ngc 6818,little gem nebula
ocl 567,ngc 2353
ic 1448,ngc 7308
ngc 6045,a 76
a 23,ngc 248
ngc 4490,cocoon galaxy
ugc 6870,ngc 3953
pk 165 15 1,ngc 1514
hrs 8,ngc 3254
gcl 54,ngc 6287
ngc 2808,gcl 13
ngc 4551,v 14
e 11,galaxy 25,ngc 3851
galaxy 19,ngc 382
ngc 14,vv 80
galaxy 28,ngc 439
the mice,mice,ngc 4676,mice galaxy
ngc 6643,n 6643
s 34,ngc 1835
gcl 97,ngc 6642
ngc 3596,hrs 42
ngc 6229,gcl 47
ngc 6553,gcl 88
lha 120 n 120,ngc 1918
ocl 495,sharpless 273,christmas tree cluster,lbn 911,ngc 2264,sh 2 273
ngc 2673,ugc 4620
galaxy 5,ngc 183
ngc 5897,gcl 33
ngc 1560,ic 2062
ngc 1855,ngc 1854
s 38,ngc 1847
ugc 1013,ngc 536
galaxy 6,ngc 194
ngc 659,ocl 332
ngc 6914,lbn 274
ngc 2073,galaxy 135
sh 2 252,ngc 2175,sharpless 252
ngc 6872,am 2011 705
ic 3568,hd 109540
lbn 807,ic 410
ic 5070,lbn 350,pelican nebula,pelican
ic 879,ic 4222
ic 290,ic 1884
ic 2599,gum 31
ic 63,lbn 622
s 26,ic 4040
ic 820,ic 819,ngc 4676 a,ngc 4676 b
lbn 813,ic 2087,ic 2087 ir
ic 444,ced 74,lbn 840
ic 1696,ic 1693
ic 349,barnard's merope nebula
lbn 620,ic 59
ic 2220,toby jug nebula
ic 360,lbn 786
ced 157 d,ic 1284
sh 2 156,sharpless 156,ic 1470
ic 2167,lbn 898,ic 446
ic 5148,ic 5150
sharpless 255,ic 2162,sh 2 255
sh 2 234,lbn 804,sharpless 234,ic 417
coddington's nebula,ic 2574
sh 2 292,ic 2177,lbn 1027,gum 1,vdb 93,rcw 2,sharpless 292
ic 610,hrs 5
ic 1795,lbn 645
ic 447,lbn 903,ic 2169
antares nebula,lbn 1107,ic 4606
ic 1623,vv 114
ic 4499,gcl 30
gingrich 1,omi per cloud,ic 348,ced 20,lbn 758,ocl 409
lbn 75,ic 1287,ced 163
gum 56,ic 4628
ic 10,lbn 591
ugc 1195,ic 148
rho oph nebula,ic 4604
sh 2 288,ic 466,sharpless 288
afgl 333 cloud,lbn 654,ic 1805,sh 2 190,sharpless 190
ic 1274,lbn 33
ic 2631,ced 112
ic 3546,ngc 4565 b
lbn 353,ic 5067
ic 5068,lbn 328
star 14,hd 202214
hd 6,hr 2
hip 379,hd 225216
sao 134031,hd 52265
sky 24,hd 224825
copernicus,hip 43587,hd 75732
hd 154301,hip 83493
hd 168459 a,hd 168459
hd 156717,hip 84792
vdb 15,hd 21389,sao 24061
hd 184738,campbell's hydrogen star
hd 150998,hip 81848
hd 206773,star 24
red rectangle,hd 44179
        """

        synonyms_rows = data.strip().split('\n')
        for row in synonyms_rows:
            synonyms = row.split(',')

            for synonym in synonyms:
                # Prepare a regex pattern for whole word matching, case-insensitive
                pattern = r'\b' + re.escape(synonym) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    return row

        return None

    @staticmethod
    def snake_to_camel(snake_str: str) -> str:
        """Helper function to convert snake_case to camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    @staticmethod
    def strip_bbcode(text):
        # This pattern matches [tag] or [/tag] or [tag=value]
        pattern = r'\[/?\w+(?:=[^\]]+)?\]'
        return re.sub(pattern, '', text)

    @staticmethod
    def detect_language(text: str) -> Optional[str]:
        """
        Detects the language of a given text. Uses a multi-level approach:
        1. Returns early if text is empty or too short
        2. Uses lingua for primary detection (with a short timeout)
        3. Falls back to langdetect if lingua fails or times out
        """

        # Quick return for empty text
        if not text or len(text.strip()) == 0:
            return None
        
        # Strip bbcode and HTML before detection
        clean_text = UtilsService.strip_bbcode(text)
        clean_text = bleach.clean(clean_text, tags=[], strip=True)
        
        # Only attempt detection if we have enough text
        clean_text = clean_text.strip()
        if len(clean_text) < 10:
            return None
        
        # Performance optimization: limit text length for detection
        # 50 chars is usually enough for accurate language detection
        # Shorter text = faster detection
        if len(clean_text) > 75:
            clean_text = clean_text[:75]
        
        # Try lingua first (with timeout protection)
        detected_language = None
        try:
            import threading
            import queue

            # Use a queue to get the result from the thread
            result_queue = queue.Queue()
            
            # Function to run detection in a thread
            def detect_with_lingua():
                try:
                    # Use the pre-initialized global detector
                    result = _LANGUAGE_DETECTOR.detect_language_of(clean_text)
                    result_queue.put(result)
                except Exception as e:
                    result_queue.put(e)
            
            # Start detection in a separate thread
            detection_thread = threading.Thread(target=detect_with_lingua)
            detection_thread.daemon = True
            
            detection_thread.start()
            
            # Wait for result with timeout (100ms)
            detection_thread.join(0.1)
            
            if detection_thread.is_alive():
                # Detection is taking too long, log and proceed to langdetect
                logger.warning(f"Lingua detection timed out after 100ms for text: '{clean_text[:30]}...'")
                # Thread will continue running, but we won't wait for it
            else:
                # Get the result from the queue
                detection_result = result_queue.get(block=False)
                
                if isinstance(detection_result, Exception):
                    # Detection raised an exception
                    logger.warning(f"Lingua threw exception: {str(detection_result)}")
                else:
                    detected_language = detection_result
        except Exception as e:
            # If thread handling fails, log and proceed to langdetect
            logger.warning(f"Thread handling error: {str(e)}")
        
        # Process lingua result if we got one
        if detected_language is not None:
            # Convert Language enum to ISO 639-1 code
            lang_code = detected_language.iso_code_639_1.name.lower()
            return lang_code

        # Fallback to langdetect (which is faster but less accurate)
        try:
            lang_code = langdetect_detect(clean_text)

            if lang_code:
                return lang_code
            else:
                # If all detection methods fail, default to English
                logger.warning(f"All language detection methods failed, defaulting to English for: '{clean_text[:30]}...'")
                return 'en'
        except (LangDetectException, Exception) as e:
            # Catch both LangDetectException and general exceptions
            logger.warning(f"Langdetect failed with error: {str(e)}")
            
            # Default to English as last resort
            return 'en'
