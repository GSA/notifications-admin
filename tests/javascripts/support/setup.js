const fs = require('fs');
const path = require('path');

// Fill in the gaps where JSDOM doesn't quite match real browsers
require('./polyfills.js');

// Make jQuery available everywhere
global.$ = global.jQuery = require('jquery');
