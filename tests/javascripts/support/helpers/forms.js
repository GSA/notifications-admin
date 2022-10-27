
// helper for spying on the submit method on a form element, via the event's `preventDefault` method
// JSDOM's implementation of requestSubmit triggers the submit event but then throws an error unless the submit handler returns false
//
// * Remove when JSDOM implements submit on its form elements *
//
// elements in JSDOM have a public API and a private implementation API, only used by internal code
// For form elements, these are instances of the following classes:
// - HTMLFormElement
// - HTMLFormElementImpl
//
// form elements link to their implementation instance via a symbol property
// this spies on the submit method of the implementation instance for a form element and mocks it to prevent 'not implemented' errors
// it returns a spy on the event preventDefault function because submit is called every time, no matter if they submission will happen or not

function spyOnFormSubmitEventPrevention (jest, form) {

  const formImplementationSymbols = Object.getOwnPropertySymbols(form).filter(
    symbol => form[symbol].constructor.name === 'HTMLFormElementImpl'
  );

  if (!formImplementationSymbols.length) {
    throw Error("Error mocking form.submit: symbol reference to HTMLFormElementImpl instance not found on form element");
  }

  const HTMLFormElementImpl = form[formImplementationSymbols[0]];

  const event = new Event("submit", {bubbles: true, cancelable: true})
  const preventDefaultSpy = jest.spyOn(event, 'preventDefault')

  const submitSpy = jest.spyOn(HTMLFormElementImpl, 'requestSubmit')
  submitSpy.mockImplementation(() => {
    form.dispatchEvent(event)
  });

  return preventDefaultSpy;
};

exports.spyOnFormSubmitEventPrevention = spyOnFormSubmitEventPrevention;
