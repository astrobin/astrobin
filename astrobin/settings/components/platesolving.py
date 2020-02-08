import os

ENABLE_SOLVING = True

PLATESOLVING_BACKENDS = (
    'astrobin_apps_platesolving.backends.astrometry_net.solver.Solver',
    'astrobin_apps_platesolving.backends.pixinsight.solver.Solver',
)

ASTROMETRY_NET_API_KEY = os.environ.get('ASTROMETRY_NET_API_KEY', 'platesolving')

PIXINSIGHT_USERNAME = os.environ.get('PIXINSIGHT_USERNAME')
PIXINSIGHT_PASSWORD = os.environ.get('PIXINSIGHT_PASSWORD')
PIXINSIGHT_USERNAME = os.environ.get('PIXINSIGHT_USERNAME')
PIXINSIGHT_PASSWORD = os.environ.get('PIXINSIGHT_PASSWORD')
