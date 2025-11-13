beforeAll(() => {
  const originalNotifyModules = window.NotifyModules;
  delete window.NotifyModules;

  require('../../app/assets/javascripts/errorBanner.js');

  expect(window.NotifyModules).toBeDefined();
  expect(window.NotifyModules.ErrorBanner).toBeDefined();
});

afterAll(() => {
    require('./support/teardown.js');
});

describe("Error Banner", () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe("The `hideBanner` method", () => {
    test("Will hide the element", () => {
      document.body.innerHTML = `
      <span class="usa-error-message banner-dangerous js-error-visible">
      </span>`;
      window.NotifyModules.ErrorBanner.hideBanner();
      expect(document.querySelector('.banner-dangerous').classList).toContain('display-none')
    });

    test("Will not error when no banner elements exist", () => {
      document.body.innerHTML = `<div>No banners here</div>`;
      expect(() => {
        window.NotifyModules.ErrorBanner.hideBanner();
      }).not.toThrow();
    });
  });

  describe("The `showBanner` method", () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <span class="usa-error-message banner-dangerous js-error-visible display-none">
        </span>`;

      window.NotifyModules.ErrorBanner.showBanner('Some Err');
    });

    test("Will show the element", () => {
      expect(document.querySelector('.banner-dangerous').classList).not.toContain('display-none')
    });

    test("Will not error when no banner elements exist", () => {
      document.body.innerHTML = `<div>No banners here</div>`;
      expect(() => {
        window.NotifyModules.ErrorBanner.showBanner();
      }).not.toThrow();
    });
  });

  test("Module exports ErrorBanner to window.NotifyModules", () => {
    expect(window.NotifyModules.ErrorBanner).toBeDefined();
    expect(window.NotifyModules.ErrorBanner.hideBanner).toBeDefined();
    expect(window.NotifyModules.ErrorBanner.showBanner).toBeDefined();
  });
});
