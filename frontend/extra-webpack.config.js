var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  plugins: [
    new BundleTracker({filename: '../astrobin/webpack-stats-angular.json'})
  ],
  output: {
    path: require('path').resolve('../astrobin/static/astrobin/bundles/frontend'),
    filename: "[name]-[hash].js"
  }
};
