const { src, dest, series } = require('gulp');
const mergeStream = require('merge-stream');
const uswds = require('@uswds/compile');
const { exec } = require('child_process');
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
  npm: 'node_modules/'
};

const javascripts = () => {
  // Files that don't use NotifyModules and can be uglified
  const local = src([
    paths.src + 'javascripts/modules/init.js',
    paths.src + 'javascripts/modules/uswds-modules.js',
    paths.src + 'javascripts/modules/show-hide-content.js',
    paths.src + 'javascripts/radioSelect.js',
    paths.src + 'javascripts/liveSearch.js',
    paths.src + 'javascripts/preventDuplicateFormSubmissions.js',
    paths.src + 'javascripts/errorBanner.js',
    paths.src + 'javascripts/notifyModal.js',
    paths.src + 'javascripts/timeoutPopup.js',
    paths.src + 'javascripts/date.js',
    paths.src + 'javascripts/loginAlert.js',
    paths.src + 'javascripts/sidenav.js',
    paths.src + 'javascripts/validation.js',
    paths.src + 'javascripts/scrollPosition.js',
  ])

  // Files that use NotifyModules - split into two groups to avoid stream issues
  const notifyModules1 = src([
    paths.src + 'javascripts/copyToClipboard.js',
    paths.src + 'javascripts/enhancedTextbox.js',
    paths.src + 'javascripts/fileUpload.js',
    paths.src + 'javascripts/errorTracking.js',
    paths.src + 'javascripts/fullscreenTable.js',
    paths.src + 'javascripts/templateFolderForm.js',
  ])
    .pipe(plugins.prettyerror())
    .pipe(
      plugins.babel({
        presets: ['@babel/preset-env'],
      })
    );

  const notifyModules2 = src([
    paths.src + 'javascripts/collapsibleCheckboxes.js',
    paths.src + 'javascripts/radioSlider.js',
    paths.src + 'javascripts/updateStatus.js',
    paths.src + 'javascripts/main.js',
  ])
    .pipe(plugins.prettyerror())
    .pipe(
      plugins.babel({
        presets: ['@babel/preset-env'],
      })
    );

  // Apply uglify only to local files
  const localUglified = local
    .pipe(
      plugins.babel({
        presets: ['@babel/preset-env'],
      })
    )
    .pipe(plugins.uglify());

  // First create vendored with jquery-expose immediately after jQuery
  const vendoredWithExpose = src([
    paths.npm + 'jquery/dist/jquery.min.js',
    paths.src + 'javascripts/jquery-expose.js',
    paths.npm + 'query-command-supported/dist/queryCommandSupported.min.js',
    paths.npm + 'textarea-caret/index.js',
    paths.npm + 'cbor-js/cbor.js',
    paths.npm + 'd3/dist/d3.min.js'
  ]);

  // Concatenate all streams
  const mainBundle = mergeStream(vendoredWithExpose, localUglified, notifyModules1, notifyModules2);

  // Use the mainBundle as the base and append remaining non-transpiled files at the end
  return mainBundle
    .pipe(plugins.addSrc.append(paths.src + 'javascripts/listEntry.js'))
    .pipe(plugins.addSrc.append(paths.src + 'javascripts/stick-to-window-when-scrolling.js'))
    .pipe(plugins.addSrc.append(paths.src + 'javascripts/totalMessagesChart.js'))
    .pipe(plugins.addSrc.append(paths.src + 'javascripts/activityChart.js'))
    .pipe(plugins.addSrc.append(paths.src + 'javascripts/job-polling.js'))
    .pipe(plugins.concat('all.js'))
    .pipe(dest(paths.dist + 'javascripts/'));
};

// Task to copy `gtm_head.js`
const copyGtmHead = () => {
  return src(paths.src + 'js/gtm_head.js').pipe(dest(paths.dist + 'js/'));
};

// Task to copy `setTimezone.js`
const copySetTimezone = () => {
  return src(paths.src + 'js/setTimezone.js').pipe(dest(paths.dist + 'js/'));
};


// Task to copy images
const copyImages = () => {
  return src(paths.src + 'images/**/*', { encoding: false }).pipe(
    dest(paths.dist + 'images/')
  );
};

// Task to pdf files
const copyPDF = () => {
  return src(paths.src + 'pdf/**/*', { encoding: false }).pipe(
    dest(paths.dist + 'pdf/')
  );
};

const copyUSWDSJS = () => {
  return src('node_modules/@uswds/uswds/dist/js/uswds.min.js')
    .pipe(dest(paths.dist + 'js/'));
};

// Configure USWDS paths
uswds.settings.version = 3;
uswds.settings.compile = {
  sass: true,
  javascript: true,
  sprites: false
};

uswds.paths.dist.css = paths.dist + 'css';
uswds.paths.dist.js = paths.dist + 'js';
uswds.paths.dist.img = paths.dist + 'img';
uswds.paths.dist.pdf = paths.dist + 'pdf';
uswds.paths.dist.fonts = paths.dist + 'fonts';
uswds.paths.dist.theme = paths.src + 'sass/uswds';

// Task to compile USWDS styles
const styles = async () => {
  await uswds.compileSass();
};

// Task to copy USWDS assetsconst
const copyUSWDSAssets = () => {
  return src([
    'node_modules/@uswds/uswds/dist/img/**/*',
    'node_modules/@uswds/uswds/dist/fonts/**/*'
  ], { encoding: false })
    .pipe(dest((file) => {
      if (file.path.includes('/img/')) {
        return paths.dist + 'img/';
      } else if (file.path.includes('/fonts/')) {
        return paths.dist + 'fonts/';
      }
      return paths.dist;
    }));
};

// Optional backstopJS task
// Install gulp globally and run `gulp backstopTest`
const backstopTest = (done) => {
  exec(
    'npx backstop test --configPath=backstop.config.js',
    (err, stdout, stderr) => {
      console.log(stdout);
      console.error(stderr);
      done(err);
    }
  );
};

// Optional backstopJS reference task
// Install gulp globally and run `gulp backstopReference`
const backstopReference = (done) => {
  exec(
    'npx backstop reference --configPath=backstop.config.js',
    (err, stdout, stderr) => {
      console.log(stdout);
      console.error(stderr);
      done(err);
    }
  );
};

// Export tasks
exports.default = series(
  styles,
  javascripts,
  copyGtmHead,
  copySetTimezone,
  copyImages,
  copyPDF,
  copyUSWDSAssets,
  copyUSWDSJS
);
exports.backstopTest = backstopTest;
exports.backstopReference = backstopReference;
