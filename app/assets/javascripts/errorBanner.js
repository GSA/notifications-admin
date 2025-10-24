export const ErrorBanner = {
  hideBanner: () => {
    document.querySelectorAll('.banner-dangerous').forEach(el => el.classList.add('display-none'));
  },
  showBanner: () => {
    document.querySelectorAll('.banner-dangerous').forEach(el => el.classList.remove('display-none'));
  }
};

window.NotifyModules = window.NotifyModules || {};
window.NotifyModules.ErrorBanner = ErrorBanner;
