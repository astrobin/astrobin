astrobin_apps_platesolving = {
    config: {
        solution: 0,
        image: 0
    },

    analyze: function() {
        alert("CIAO");
    },

    init: function(config) {
        astrobin_apps_platesolving.config.solution = config.solution;
        astrobin_apps_platesolving.config.image = config.image;
    }
};
