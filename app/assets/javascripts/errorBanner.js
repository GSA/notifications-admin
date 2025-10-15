export const ErrorBanner = {
  hideBanner: () => $('.banner-dangerous').addClass('display-none'),
  showBanner: () => $('.banner-dangerous').removeClass('display-none')
};

window.NotifyModules = window.NotifyModules || {};
window.NotifyModules.ErrorBanner = ErrorBanner;
