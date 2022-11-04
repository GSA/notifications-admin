module.exports = {
  setupFiles: ['./support/setup.js'],
  testEnvironment: 'jsdom',
  testEnvironmentOptions: {
    url: 'https://www.notifications.service.gov.uk',
  },
}
