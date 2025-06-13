// Polyfills for JSDOM

// Fix for JSDOM v22 location object being non-configurable
delete window.location;
window.location = Object.assign(new URL("https://beta.notify.gov"), {
  reload: jest.fn(),
  assign: jest.fn(),
  replace: jest.fn(),
});
