PIPELINE = {
    'PIPELINE_ENABLED': not DEBUG,
    'PIPELINE_COLLECTOR_ENABLED': False,
    'SHOW_ERRORS_INLINE': True,

    'JAVASCRIPT': {
        'scripts': {
            'source_filenames': (
                'common/fancybox/jquery.fancybox.js',

                'astrobin_apps_images/js/astrobin_apps_images.js',

                'astrobin/js/jquery.i18n.js',
                'astrobin/js/plugins/localization/jquery.localisation.js',
                'astrobin/js/jquery.uniform.js',
                'astrobin/js/jquery-ui-1.10.3.custom.min.js',
                'astrobin/js/jquery-ui-timepicker-addon.js',
                'astrobin/js/jquery.validationEngine-en.js',
                'astrobin/js/jquery.validationEngine.js',
                'astrobin/js/jquery.autoSuggest.js',
                'astrobin/js/jquery.blockUI.js',
                'astrobin/js/jquery.tmpl.1.1.1.js',
                'astrobin/js/ui.multiselect.js',
                'astrobin/js/jquery.form.js',
                'astrobin/js/jquery.tokeninput.js',
                'astrobin/js/jquery.flot.js',
                'astrobin/js/jquery.flot.pie.min.js',
                'astrobin/js/jquery.cycle.all.js',
                'astrobin/js/jquery.easing.1.3.js',
                'astrobin/js/jquery.multiselect.js',
                'astrobin/js/jquery.qtip.js',
                'astrobin/js/jquery.stickytableheaders.js',
                'astrobin/js/jquery.timeago.js',
                'astrobin/js/respond.src.js',
                'astrobin/wysibb/jquery.wysibb.js',
                'astrobin/js/astrobin.js',
            ),
            'output_filename': 'astrobin/js/astrobin_bundle.js',
        },
        'landing': {
            'source_filenames': (
                'astrobin_apps_landing/js/jquery-3.0.0.min.js',
                'astrobin_apps_landing/js/jquery-migrate-3.0.0.min.js',
                'astrobin_apps_landing/js/popper.min.js',
                'astrobin_apps_landing/js/bootstrap.min.js',
                'astrobin_apps_landing/js/scrollIt.min.js',
                'astrobin_apps_landing/js/jquery.waypoints.min.js',
                'astrobin_apps_landing/js/jquery.counterup.min.js',
                'astrobin_apps_landing/js/owl.carousel.min.js',
                'astrobin_apps_landing/js/jquery.magnific-popup.min.js',
                'astrobin_apps_landing/js/jquery.stellar.min.js',
                'astrobin_apps_landing/js/isotope.pkgd.min.js',
                'astrobin_apps_landing/js/YouTubePopUp.jquery.js',
                'astrobin_apps_landing/js/particles.min.js',
                'astrobin_apps_landing/js/app.js',
                'astrobin_apps_landing/js/map.js',
                'astrobin_apps_landing/js/validator.js',
                'astrobin_apps_landing/js/scripts.js',
            ),
            'output_filename': 'astrobin/js/astrobin_landing.js',
        }
    },
    'STYLESHEETS': {
        'screen': {
            'source_filenames': (
                'astrobin/css/jquery-ui.css',
                'astrobin/css/jquery-ui-astrobin/jquery-ui-1.8.17.custom.css',
                'astrobin/css/ui.multiselect.css',
                'astrobin/css/validationEngine.jquery.css',
                'astrobin/css/token-input.css',
                'astrobin/css/jquery.multiselect.css',
                'astrobin/css/jquery.qtip.css',

                'astrobin/wysibb/theme/default/wbbtheme.css',

                'astrobin_apps_donations/css/astrobin_apps_donations.css',
                'astrobin_apps_premium/css/astrobin_apps_premium.css',

                'astrobin/css/reset.css',
                'astrobin/css/bootstrap.css',
                'astrobin/css/bootstrap-responsive.css',

                'common/fancybox/jquery.fancybox.css',

                'astrobin/scss/astrobin.scss',
                'astrobin/scss/astrobin-mobile.scss',
            ),
            'output_filename': 'astrobin/css/astrobin_screen.css',
            'extra_content':  {
                'media': 'screen, projection',
            },
        },
        'landing': {
            'source_filenames': {
                'astrobin_apps_landing/css/plugins.css',
                'astrobin_apps_landing/css/style.css'
            },
            'output_filename': 'astrobin_css/astrobin_landing.css',
             'extra_content':  {
                'media': 'screen, projection',
            },
        }
    },
    'COMPILERS': (
        'pipeline.compilers.sass.SASSCompiler',
    ),
    'CSS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'JS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
}

