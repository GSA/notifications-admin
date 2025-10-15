const modules = new Map();

export function registerModule(name, ModuleClass) {
  modules.set(name, ModuleClass);
  window.NotifyModules = window.NotifyModules || {};
  window.NotifyModules[name] = ModuleClass;
}

export function initModules() {
  const moduleElements = document.querySelectorAll('[data-module]');

  moduleElements.forEach(element => {
    const moduleName = element.getAttribute('data-module');
    const moduleStarted = element.getAttribute('data-module-started');

    if (moduleStarted) return;

    const ModuleClass = modules.get(moduleName);

    if (!ModuleClass) {
      console.warn(`Module "${moduleName}" not found in registry`);
      return;
    }

    try {
      const moduleInstance = new ModuleClass();

      if (moduleInstance.start && typeof moduleInstance.start === 'function') {
        moduleInstance.start(element);
      }

      element.setAttribute('data-module-started', 'true');
    } catch (error) {
      console.error(`Error initializing module "${moduleName}":`, error);
    }
  });
}

window.NotifyModules = window.NotifyModules || {};
window.NotifyModules.start = initModules;
