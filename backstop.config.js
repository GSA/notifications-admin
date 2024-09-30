const { urls, baseUrl } = require('./urls');

const createScenariosFromUrls = (urls, delay = 1000) => {
  return Object.keys(urls).map((label) => ({
    label,
    url: urls[label],
    selectors: ['document'],
    misMatchThreshold: 0.3,
    requireSameDimensions: true,
    delay,
  }));
};

module.exports = {
  id: 'backstop_test',
  viewports: [
    {
      label: 'desktop',
      width: 1024,
      height: 768,
    },
  ],
  scenarios: [
    ...createScenariosFromUrls(urls),
    {
      label: 'Choose Service - Accounts',
      url: `${baseUrl}/accounts`,
      selectors: ['h1.heading-large', 'a.usa-button[href="/add-service"]'],
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
    },
    // example page with script
    {
      label: 'Get Started Page - Highlight Trial Mode',
      url: `${baseUrl}/using-notify/get-started`,
      selectors: ['document'],
      misMatchThreshold: 0.1,
      requireSameDimensions: true,
      onBeforeScript: 'puppeteer/countFeatureLinks.js',
    },
  ],
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
  debug: false,
};
