const fs = require('fs');
const path = require('path');

// Fill in the gaps where JSDOM doesn't quite match real browsers
require('./polyfills.js');

// Make jQuery available everywhere
global.$ = global.jQuery = require('jquery');

// Bring in the GOV.UK modules system
require('govuk_frontend_toolkit/javascripts/govuk/modules.js');
