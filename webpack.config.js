const path = require('path');

module.exports = {
  mode: 'development', // Switch to 'production' later

  entry: {
    // Temporary test entry - will be replaced with proper entry in Phase 2
    test: path.resolve(__dirname, 'app/assets/javascripts/modules/init.js')
  },

  output: {
    path: path.resolve(__dirname, 'app/static-webpack'), // Separate output for testing
    filename: '[name].bundle.js',
    clean: true // Clean output directory before each build
  },

  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      }
    ]
  },

  resolve: {
    extensions: ['.js'],
    alias: {
      // Aliases for cleaner imports later
      '@javascripts': path.resolve(__dirname, 'app/assets/javascripts'),
      '@modules': path.resolve(__dirname, 'app/assets/javascripts/modules')
    }
  },

  // Source maps for debugging
  devtool: 'source-map',

  stats: {
    colors: true,
    modules: false,
    children: false,
    chunks: false,
    chunkModules: false
  }
};
