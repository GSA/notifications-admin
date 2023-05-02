module.exports = {
  collectCoverage: true,
  coverageDirectory: './coverage',
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 90,
      lines: 90,
      statements: 90,
    }
  },
  setupFiles: ['./support/setup.js'],
  testEnvironment: 'jsdom',
  testEnvironmentOptions: {
    url: 'https://www.notifications.service.gov.uk',
  },
};
