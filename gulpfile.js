const { src, dest, series, parallel, watch } = require('gulp');
const rollup = require('@rollup/stream');
const rollupPluginCommonjs = require('@rollup/plugin-commonjs');
const rollupPluginNodeResolve = require('@rollup/plugin-node-resolve');
const source = require('vinyl-source-stream');
const buffer = require('vinyl-buffer');
const gulpMerge = require('gulp-merge');
const stylish = require('jshint-stylish');
const uswds = require("@uswds/compile");

const plugins = {};
plugins.addSrc = require('gulp-add-src');
plugins.babel = require('gulp-babel');
plugins.cleanCSS = require('gulp-clean-css');
plugins.concat = require('gulp-concat');
plugins.jshint = require('gulp-jshint');
plugins.prettyerror = require('gulp-prettyerror');
plugins.uglify = require('gulp-uglify');

const paths = {
  src: 'app/assets/',
  dist: 'app/static/',
  npm: 'node_modules/',
  toolkit: 'node_modules/govuk_frontend_toolkit/',
  govuk_frontend: 'node_modules/govuk-frontend/'
};

const javascripts = () => {
  const vendored = rollup({
    input: paths.src + 'javascripts/modules/all.mjs',
    plugins: [
      rollupPluginNodeResolve({
        mainFields: ['module', 'main']
      }),
      rollupPluginCommonjs({
        include: 'node_modules/**'
      })
    ],
    output: {
      format: 'iife',
      name: 'GOVUK'
    }
  })
    .pipe(source('all.mjs'))
    .pipe(buffer())
    .pipe(plugins.addSrc.prepend([
      paths.npm + 'hogan.js/dist/hogan-3.0.2.js',
      paths.npm + 'jquery/dist/jquery.min.js',
      paths.npm + 'query-command-supported/dist/queryCommandSupported.min.js',
      paths.npm + 'timeago/jquery.timeago.js',
      paths.npm + 'textarea-caret/index.js',
      paths.npm + 'cbor-js/cbor.js',
      paths.npm + 'socket.io-client/dist/socket.io.min.js',
      paths.npm + 'chart.js/dist/chart.umd.js'
    ]));

  const local = src([
    paths.toolkit + 'javascripts/govuk/modules.js',
    paths.toolkit + 'javascripts/govuk/show-hide-content.js',
    paths.src + 'javascripts/copyToClipboard.js',
    paths.src + 'javascripts/autofocus.js',
    paths.src + 'javascripts/enhancedTextbox.js',
    paths.src + 'javascripts/fileUpload.js',
    paths.src + 'javascripts/radioSelect.js',
    paths.src + 'javascripts/updateContent.js',
    paths.src + 'javascripts/listEntry.js',
    paths.src + 'javascripts/liveSearch.js',
    paths.src + 'javascripts/errorTracking.js',
    paths.src + 'javascripts/preventDuplicateFormSubmissions.js',
    paths.src + 'javascripts/fullscreenTable.js',
    paths.src + 'javascripts/colourPreview.js',
    paths.src + 'javascripts/templateFolderForm.js',
    paths.src + 'javascripts/collapsibleCheckboxes.js',
    paths.src + 'javascripts/radioSlider.js',
    paths.src + 'javascripts/updateStatus.js',
    paths.src + 'javascripts/errorBanner.js',
    paths.src + 'javascripts/homepage.js',
    paths.src + 'javascripts/timeoutPopup.js',
    paths.src + 'javascripts/date.js',
    paths.src + 'javascripts/loginAlert.js',
    paths.src + 'javascripts/main.js',
    paths.src + 'javascripts/sampleChartDashboard.js',
  ])
    .pipe(plugins.prettyerror())
    .pipe(plugins.babel({
      presets: ['@babel/preset-env']
    }));

  return gulpMerge(vendored, local)
    .pipe(plugins.uglify())
    .pipe(plugins.concat('all.js'))
    .pipe(dest(paths.dist + 'javascripts/'));
};

exports.default = series(javascripts);
