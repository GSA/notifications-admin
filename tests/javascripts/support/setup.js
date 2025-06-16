const fs = require('fs');
const path = require('path');

// Set up jQuery
global.$ = global.jQuery = require('jquery');

// Load module code
require('govuk_frontend_toolkit/javascripts/govuk/modules.js');
