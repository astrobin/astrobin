const webpack = require("webpack");

module.exports = {
  watchOptions: {
    ignored: /node_modules/
  },
  plugins: [
    new webpack.DefinePlugin({
      VERSION: new Date().getTime()
    })
  ]
};
