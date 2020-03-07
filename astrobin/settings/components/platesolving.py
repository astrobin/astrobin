import os

ENABLE_SOLVING = True
PLATESOLVING_BACKEND = \
    'astrobin_apps_platesolving.backends.astrometry_net.solver.Solver'
ASTROMETRY_NET_API_KEY = os.environ.get('ASTROMETRY_NET_API_KEY', 'platesolving').strip()

