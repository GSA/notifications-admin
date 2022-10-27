// Polyfills for any parts of the DOM API available in browsers but not JSDOM

let _location = {
  reload: jest.fn(),
  hostname: "www.notifications.service.gov.uk",
  assign: jest.fn(),
  href: "https://www.notifications.service.gov.uk",
}

// JSDOM provides a read-only window.location, which does not allow for
// mocking or setting.
Object.defineProperty(window, 'location', {
  get: () => _location,
  set: (value) => {
    _location = value
  },
})
