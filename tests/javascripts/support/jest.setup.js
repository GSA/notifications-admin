const fs = require('fs');
const path = require('path');

// Set up jQuery
global.$ = global.jQuery = require('jquery');

// tests/jest.setup.js
global.io = jest.fn().mockReturnValue({
  on: jest.fn(),
  emit: jest.fn(),
});

// Load module code
global.window = global.window || {};
global.window.NotifyModules = global.window.NotifyModules || {};
global.window.NotifyModules.start = function() {
  var modules = document.querySelectorAll('[data-module]');
  modules.forEach(function(element) {
    var moduleName = element.getAttribute('data-module');
    var moduleStarted = element.getAttribute('data-module-started');

    if (!moduleStarted && global.window.NotifyModules[moduleName]) {
      var module = new global.window.NotifyModules[moduleName]();
      if (module.start) {
        module.start(element);
      }
      element.setAttribute('data-module-started', 'true');
    }
  });
};
