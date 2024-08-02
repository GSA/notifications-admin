const fs = require('fs');
const path = require('path');

// Polyfill holes in JSDOM
require('./polyfills.js');

// Set up jQuery
global.$ = global.jQuery = require('jquery');

// tests/jest.setup.js
global.io = jest.fn().mockReturnValue({
    on: jest.fn(),
    emit: jest.fn()
});

// Load module code
require('govuk_frontend_toolkit/javascripts/govuk/modules.js');
