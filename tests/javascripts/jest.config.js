module.exports = {
  collectCoverage: true,
  coverageDirectory: './coverage',
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 90,
      lines: 90,
      statements: 90,
    }
  },
  setupFiles: ['./support/setup.js'],
  testEnvironment: 'jsdom',
  testEnvironmentOptions: {
    url: 'https://beta.notify.gov',
  },
};
