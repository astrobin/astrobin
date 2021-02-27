const webpack = require("webpack");

module.exports = {
  plugins: [
    new webpack.DefinePlugin({
      VERSION: new Date().getTime()
    })
  ]
};
