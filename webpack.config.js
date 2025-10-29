const path = require('path');
const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');
const CopyPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  mode: isProduction ? 'production' : 'development',

  entry: {
    all: path.resolve(__dirname, 'app/assets/javascripts/index.js'),
    styles: path.resolve(__dirname, 'app/assets/sass/uswds/styles.scss')
  },

  output: {
    path: path.resolve(__dirname, 'app/static/javascripts'),
    filename: '[name].js',
    clean: true
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
      },
      {
        test: /\.s[ac]ss$/i,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              url: false
            }
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [require('autoprefixer')]
              }
            }
          },
          {
            loader: 'sass-loader',
            options: {
              sassOptions: {
                loadPaths: [
                  path.resolve(__dirname, 'app/assets/sass/uswds'),
                  path.resolve(__dirname, 'node_modules/@uswds'),
                  path.resolve(__dirname, 'node_modules/@uswds/uswds/packages'),
                  path.resolve(__dirname, 'node_modules/@uswds/uswds/dist/scss/stylesheets/packages')
                ]
              }
            }
          }
        ]
      }
    ]
  },

  resolve: {
    extensions: ['.js'],
    alias: {
      '@javascripts': path.resolve(__dirname, 'app/assets/javascripts'),
      '@modules': path.resolve(__dirname, 'app/assets/javascripts/modules')
    }
  },

  plugins: [
    new MiniCssExtractPlugin({
      filename: '../css/styles.css'
    }),
    new CopyPlugin({
      patterns: [
        {
          from: path.resolve(__dirname, 'app/assets/images'),
          to: path.resolve(__dirname, 'app/static/images'),
          noErrorOnMissing: true
        },
        {
          from: path.resolve(__dirname, 'app/assets/pdf'),
          to: path.resolve(__dirname, 'app/static/pdf'),
          noErrorOnMissing: true
        },
        {
          from: path.resolve(__dirname, 'app/assets/js/gtm_head.js'),
          to: path.resolve(__dirname, 'app/static/js/gtm_head.js'),
          noErrorOnMissing: true
        },
        {
          from: path.resolve(__dirname, 'app/assets/js/setTimezone.js'),
          to: path.resolve(__dirname, 'app/static/js/setTimezone.js'),
          noErrorOnMissing: true
        },
        {
          from: path.resolve(__dirname, 'node_modules/@uswds/uswds/dist/js/uswds.min.js'),
          to: path.resolve(__dirname, 'app/static/js/uswds.min.js')
        },
        {
          from: path.resolve(__dirname, 'node_modules/@uswds/uswds/dist/fonts'),
          to: path.resolve(__dirname, 'app/static/fonts')
        },
        {
          from: path.resolve(__dirname, 'node_modules/@uswds/uswds/dist/img'),
          to: path.resolve(__dirname, 'app/static/img')
        }
      ]
    })
  ],

  optimization: {
    minimize: isProduction,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: isProduction,
            drop_debugger: true,
            pure_funcs: isProduction ? ['console.info', 'console.debug', 'console.warn', 'console.error'] : [],
          },
          mangle: true,
          format: {
            comments: false,
          },
        },
        extractComments: false,
      }),
    ],
    splitChunks: false,
  },

  devtool: isProduction ? false : 'source-map',

  stats: {
    colors: true,
    modules: false,
    children: false,
    chunks: false,
    chunkModules: false
  },

  performance: {
    hints: isProduction ? 'warning' : false,
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
  }
};
