import os

WEBPACK_LOADER = {
    'FRONTEND': {
        'BUNDLE_DIR_NAME': 'astrobin/bundles/frontend/',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats-angular.json'),
    }
}
