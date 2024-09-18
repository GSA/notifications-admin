const { urls } = require('./urls');

// Helper function to automatically generate scenarios from the URLs
const createScenariosFromUrls = (urlsObj, delay = 1000) => {
  return Object.keys(urlsObj).map((label) => ({
    label,
    url: urlsObj[label],
    hideSelectors: [],
    removeSelectors: [],
    selectors: ['document'],
    selectorExpansion: true,
    misMatchThreshold: 0.1,
    requireSameDimensions: true,
    delay,
  }));
};

module.exports = {
  id: 'my_project_tests',
  viewports: [
    {
      label: 'desktop',
      width: 1024,
      height: 768,
    },
  ],
  scenarios: createScenariosFromUrls(urls),
  paths: {
    bitmaps_reference: 'backstop_data/bitmaps_reference',
    bitmaps_test: 'backstop_data/bitmaps_test',
    engine_scripts: 'backstop_data/engine_scripts',
    html_report: 'backstop_data/html_report',
    ci_report: 'backstop_data/ci_report',
  },
  engine: 'puppeteer',
  engineOptions: {
    browser: 'chromium',
    timeout: 30000,
  },
  report: ['browser'],
  debug: true,
};
