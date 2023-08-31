// GULPFILE
// - - - - - - - - - - - - - - -
// This file processes all of the assets in the "src" folder
// and outputs the finished files in the "dist" folder.

// 1. LIBRARIES
// - - - - - - - - - - - - - - -
const { src, pipe, dest, series, parallel, watch } = require('gulp');
const rollupPluginCommonjs = require('rollup-plugin-commonjs');
const rollupPluginNodeResolve = require('rollup-plugin-node-resolve');
const streamqueue = require('streamqueue');
const stylish = require('jshint-stylish');
const uswds = require("@uswds/compile");

const plugins = {};
plugins.addSrc = require('gulp-add-src');
plugins.babel = require('gulp-babel');
plugins.cleanCSS = require('gulp-clean-css');
plugins.concat = require('gulp-concat');
plugins.cssUrlAdjuster = require('gulp-css-url-adjuster');
plugins.jshint = require('gulp-jshint');
plugins.prettyerror = require('gulp-prettyerror');
plugins.rollup = require('gulp-better-rollup')
plugins.uglify = require('gulp-uglify');

// 2. CONFIGURATION
// - - - - - - - - - - - - - - -
const paths = {
  src: 'app/assets/',
  dist: 'app/static/',
  templates: 'app/templates/',
  npm: 'node_modules/',
  toolkit: 'node_modules/govuk_frontend_toolkit/',
  govuk_frontend: 'node_modules/govuk-frontend/'
};
// Rewrite /static prefix for URLs in CSS files
let staticPathMatcher = new RegExp('^\/static\/');
if (process.env.NOTIFY_ENVIRONMENT == 'development') { // pass through if on development
  staticPathMatcher = url => url;
}

// 3. TASKS
// - - - - - - - - - - - - - - -

// Move GOV.UK template resources

const copy = {
  error_pages: () => {
    return src(paths.src + 'error_pages/**/*')
      .pipe(dest(paths.dist + 'error_pages/'))
  },
  fonts: () => {
    return src(paths.src + 'fonts/**/*')
      .pipe(dest(paths.dist + 'fonts/'));
  },
  gtm: () => {
    return src(paths.src + 'js/gtm_head.js')
      .pipe(dest(paths.dist + 'js/'));
  }
};




const javascripts = () => {
  // JS from third-party sources
  // We assume none of it will need to pass through Babel
  const vendored = src(paths.src + 'javascripts/modules/all.mjs')
    // Use Rollup to combine all JS in JS module format into a Immediately Invoked Function
    // Expression (IIFE) to:
    // - deliver it in one bundle
    // - allow it to run in browsers without support for JS Modules
    .pipe(plugins.rollup(
      {
        plugins: [
          // determine module entry points from either 'module' or 'main' fields in package.json
          rollupPluginNodeResolve({
            mainFields: ['module', 'main']
          }),
          // gulp rollup runs on nodeJS so reads modules in commonJS format
          // this adds node_modules to the require path so it can find the GOVUK Frontend modules
          rollupPluginCommonjs({
            include: 'node_modules/**'
          })
        ]
      },
      {
        format: 'iife',
        name: 'GOVUK'
      }
    ))
    // return a stream which pipes these files before the JS modules bundle
    .pipe(plugins.addSrc.prepend([
      paths.npm + 'hogan.js/dist/hogan-3.0.2.js',
      paths.npm + 'jquery/dist/jquery.min.js',
      paths.npm + 'query-command-supported/dist/queryCommandSupported.min.js',
      paths.npm + 'timeago/jquery.timeago.js',
      paths.npm + 'textarea-caret/index.js',
      paths.npm + 'cbor-js/cbor.js'
    ]));

  // JS local to this application
  const local = src([
    paths.toolkit + 'javascripts/govuk/modules.js',
    paths.toolkit + 'javascripts/govuk/show-hide-content.js',
    paths.src + 'javascripts/govuk/cookie-functions.js',
    paths.src + 'javascripts/consent.js',
    paths.src + 'javascripts/cookieMessage.js',
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
    paths.src + 'javascripts/previewPane.js',
    paths.src + 'javascripts/colourPreview.js',
    paths.src + 'javascripts/templateFolderForm.js',
    paths.src + 'javascripts/collapsibleCheckboxes.js',
    paths.src + 'javascripts/radioSlider.js',
    paths.src + 'javascripts/updateStatus.js',
    paths.src + 'javascripts/errorBanner.js',
    paths.src + 'javascripts/homepage.js',
    paths.src + 'javascripts/main.js',
  ])
    .pipe(plugins.prettyerror())
    .pipe(plugins.babel({
      presets: ['@babel/preset-env']
    }));

  // return single stream of all vinyl objects piped from the end of the vendored stream, then
  // those from the end of the local stream
  return streamqueue({ objectMode: true }, vendored, local)
    .pipe(plugins.uglify())
    .pipe(plugins.concat('all.js'))
    .pipe(dest(paths.dist + 'javascripts/'))
};


// Copy images

const images = () => {
  return src([
    paths.toolkit + 'images/**/*',
    paths.govuk_frontend + 'assets/images/**/*',
    paths.src + 'images/**/*',
    paths.src + 'img/**/*',
    paths.template + 'assets/images/**/*'

  ])
    .pipe(dest(paths.dist + 'images/'))
};


const watchFiles = {
  javascripts: (cb) => {
    watch([paths.src + 'javascripts/**/*'], javascripts);
    cb();
  },
  images: (cb) => {
    watch([paths.src + 'images/**/*'], images);
    cb();
  },
  uswds: (cb) => {
    watch([paths.src + 'sass/**/*'], uswds.watch);
    cb();
  },
  self: (cb) => {
    watch(['gulpfile.js'], defaultTask);
    cb();
  }
};


const lint = {
  'js': (cb) => {
    return src(
      paths.src + 'javascripts/**/*.js'
    )
      .pipe(plugins.jshint())
      .pipe(plugins.jshint.reporter(stylish))
      .pipe(plugins.jshint.reporter('fail'))
  }
};


// Default: compile everything
const defaultTask = parallel(
  parallel(
    copy.fonts,
    images
  ),
  series(
    copy.error_pages,
    series(
      javascripts
    ),
    uswds.compile,
    uswds.copyAssets,
    copy.gtm
  )
);


// Watch for changes and re-run tasks
const watchForChanges = parallel(
  watchFiles.javascripts,
  watchFiles.images,
  watchFiles.self
);


exports.default = defaultTask;

exports.lint = series(lint.js);

// Optional: recompile on changes
exports.watch = series(defaultTask, watchForChanges);


// 3. Compile USWDS

/**
* USWDS version
* Set the major version of USWDS you're using
* (Current options are the numbers 2 or 3)
*/
uswds.settings.version = 3;

/**
* Path settings
* Set as many as you need
*/
uswds.paths.dist.css = './app/static/css';
uswds.paths.dist.js = './app/static/js';
uswds.paths.dist.img = './app/static/img';
uswds.paths.dist.fonts = './app/static/fonts';
uswds.paths.dist.theme = './app/assets/sass/uswds';

/**
* Exports
* Add as many as you need
*/
exports.init = uswds.init;
exports.compile = uswds.compile;
exports.copyAll = uswds.copyAll;
exports.watch = uswds.watch;
exports.copyAssets = uswds.copyAssets;
